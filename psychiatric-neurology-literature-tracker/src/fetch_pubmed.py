import os
import time
import json
import html
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from typing import Dict, List, Any

import requests
import yaml

from score_papers import score_paper, classify_priority

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def load_config(config_path: str = "config/topics.yml") -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def search_pubmed(query: str, days_back: int, max_results: int, sort: str, tool_name: str) -> List[str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results,
        "sort": sort,
        "datetype": "pdat",
        "reldate": days_back,
        "tool": tool_name,
        "email": os.getenv("NCBI_EMAIL", "your_email@example.com"),
    }

    api_key = os.getenv("NCBI_API_KEY")
    if api_key:
        params["api_key"] = api_key

    response = requests.get(ESEARCH_URL, params=params, timeout=40)
    response.raise_for_status()
    data = response.json()
    return data.get("esearchresult", {}).get("idlist", [])


def _text_or_empty(node) -> str:
    if node is None:
        return ""
    return "".join(node.itertext()).strip()


def _article_date(article) -> str:
    # Try ArticleDate first
    ad = article.find(".//ArticleDate")
    if ad is not None:
        y = _text_or_empty(ad.find("Year"))
        m = _text_or_empty(ad.find("Month"))
        d = _text_or_empty(ad.find("Day"))
        return "-".join([x for x in [y, m.zfill(2) if m else "", d.zfill(2) if d else ""] if x])

    # Fallback to Journal Issue PubDate
    pd = article.find(".//JournalIssue/PubDate")
    if pd is not None:
        y = _text_or_empty(pd.find("Year"))
        m = _text_or_empty(pd.find("Month"))
        d = _text_or_empty(pd.find("Day"))
        return " ".join([x for x in [y, m, d] if x])
    return ""


def _extract_doi(article) -> str:
    for aid in article.findall(".//ArticleId"):
        if aid.attrib.get("IdType") == "doi":
            return _text_or_empty(aid)
    for eid in article.findall(".//ELocationID"):
        if eid.attrib.get("EIdType") == "doi":
            return _text_or_empty(eid)
    return ""


def fetch_details(pmids: List[str]) -> List[Dict[str, Any]]:
    if not pmids:
        return []

    results = []
    batch_size = 100
    for i in range(0, len(pmids), batch_size):
        batch = pmids[i:i + batch_size]
        params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "xml",
            "tool": "psychiatric_neurology_tracker",
            "email": os.getenv("NCBI_EMAIL", "your_email@example.com"),
        }

        api_key = os.getenv("NCBI_API_KEY")
        if api_key:
            params["api_key"] = api_key

        response = requests.get(EFETCH_URL, params=params, timeout=60)
        response.raise_for_status()

        root = ET.fromstring(response.text)
        for article in root.findall(".//PubmedArticle"):
            pmid = _text_or_empty(article.find(".//PMID"))
            title = html.unescape(_text_or_empty(article.find(".//ArticleTitle")))
            abstract_parts = article.findall(".//Abstract/AbstractText")
            abstract = "\n".join(html.unescape(_text_or_empty(x)) for x in abstract_parts if _text_or_empty(x))
            journal = html.unescape(_text_or_empty(article.find(".//Journal/Title")))
            pub_date = _article_date(article)
            doi = _extract_doi(article)

            results.append({
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "journal": journal,
                "pub_date": pub_date,
                "doi": doi,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
            })

        time.sleep(0.34)

    return results


def collect_papers(config_path: str = "config/topics.yml") -> List[Dict[str, Any]]:
    config = load_config(config_path)
    settings = config.get("search_settings", {})
    days_back = int(settings.get("days_back", 7))
    max_results = int(settings.get("max_results_per_topic", 30))
    sort = settings.get("sort", "pub_date")
    tool_name = settings.get("tool_name", "psychiatric_neurology_tracker")

    topic_map = {}
    pmid_to_topics = {}

    for topic in config.get("topics", []):
        print(f"Searching topic: {topic['name']}")
        try:
            pmids = search_pubmed(
                query=topic["query"],
                days_back=days_back,
                max_results=max_results,
                sort=sort,
                tool_name=tool_name,
            )
        except Exception as e:
            print(f"Warning: failed topic {topic['id']}: {e}")
            continue

        topic_map[topic["id"]] = topic
        for pmid in pmids:
            pmid_to_topics.setdefault(pmid, []).append({
                "id": topic["id"],
                "name": topic["name"],
                "priority": int(topic.get("priority", 3)),
            })

        time.sleep(0.34)

    all_pmids = list(pmid_to_topics.keys())
    details = fetch_details(all_pmids)

    exclude_terms = [x.lower() for x in config.get("exclude_keywords", [])]

    papers = []
    for paper in details:
        topics = pmid_to_topics.get(paper["pmid"], [])
        topic_priority = max([t.get("priority", 3) for t in topics], default=3)
        text_for_filter = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()

        # Do not fully remove excluded terms; only downgrade later. But skip if almost surely irrelevant.
        if any(term in text_for_filter for term in exclude_terms) and not any(
            key in text_for_filter for key in ["clinical", "patient", "cohort", "case", "dementia"]
        ):
            continue

        score = score_paper(paper.get("title", ""), paper.get("abstract", ""), topic_priority=topic_priority)
        paper["topics"] = topics
        paper["score"] = score
        paper["priority_label"] = classify_priority(score)
        papers.append(paper)

    papers.sort(key=lambda x: x.get("score", 0), reverse=True)
    return papers


def save_papers(papers: List[Dict[str, Any]]) -> Path:
    Path("data").mkdir(exist_ok=True)
    output_path = Path("data") / f"papers_{date.today().isoformat()}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    return output_path


if __name__ == "__main__":
    papers = collect_papers()
    path = save_papers(papers)
    print(f"Saved {len(papers)} papers to {path}")
