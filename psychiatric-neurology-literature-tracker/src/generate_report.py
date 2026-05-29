import json
from datetime import date
from pathlib import Path
from typing import List, Dict, Any

from fetch_pubmed import collect_papers, save_papers, load_config
from summarize_deepseek import summarize_paper_with_deepseek


def md_escape(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def short_abstract(text: str, n: int = 350) -> str:
    text = (text or "").strip().replace("\n", " ")
    if len(text) <= n:
        return text
    return text[:n].rstrip() + "..."


def make_report(papers: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
    today = date.today().isoformat()
    project_name = config.get("project_name", "Psychiatric-Neurology Literature Tracker")
    report_settings = config.get("report_settings", {})
    top_n = int(report_settings.get("top_n_must_read", 5))
    include_low = bool(report_settings.get("include_low_priority", False))

    ai_settings = config.get("ai_settings", {})
    max_summaries = int(ai_settings.get("max_papers_to_summarize", 10))

    visible_papers = papers if include_low else [p for p in papers if p.get("priority_label") != "低优先级"]

    lines = []
    lines.append(f"# {project_name} 周报")
    lines.append("")
    lines.append(f"生成日期：{today}")
    lines.append("")
    lines.append("> 定位：精神科专科医院中的神经内科临床与科研文献追踪。重点关注神经退行性疾病、精神行为症状、器质性精神障碍鉴别、精神科药物相关神经系统问题、影像与生物标志物。")
    lines.append("")

    lines.append("## 一、本周最值得读的文章")
    lines.append("")
    if not visible_papers:
        lines.append("本周期内未检索到符合条件的文献。")
    else:
        lines.append("| 优先级 | 评分 | 题目 | 期刊 | PMID |")
        lines.append("|---|---:|---|---|---|")
        for p in visible_papers[:top_n]:
            lines.append(
                f"| {p.get('priority_label')} | {p.get('score')} | "
                f"[{md_escape(p.get('title'))}]({p.get('url')}) | "
                f"{md_escape(p.get('journal'))} | {p.get('pmid')} |"
            )
    lines.append("")

    lines.append("## 二、AI 中文临床总结")
    lines.append("")
    if not visible_papers:
        lines.append("无。")
    else:
        for idx, p in enumerate(visible_papers[:max_summaries], start=1):
            topic_names = "、".join([t.get("name", "") for t in p.get("topics", [])])
            lines.append(f"### {idx}. {p.get('title')}")
            lines.append("")
            lines.append(f"- 期刊：{p.get('journal', '')}")
            lines.append(f"- 发表日期：{p.get('pub_date', '')}")
            lines.append(f"- PMID：[{p.get('pmid')}]({p.get('url')})")
            lines.append(f"- 主题：{topic_names}")
            lines.append(f"- 自动评分：{p.get('score')}（{p.get('priority_label')}）")
            lines.append("")
            try:
                summary = summarize_paper_with_deepseek(p, config)
            except Exception as e:
                summary = f"AI 总结失败：{e}\n\n基础摘要：{short_abstract(p.get('abstract', ''))}"
            lines.append(summary)
            lines.append("")

    lines.append("## 三、按主题归类")
    lines.append("")
    topic_to_papers = {}
    for p in visible_papers:
        for t in p.get("topics", []):
            topic_to_papers.setdefault(t.get("name", "未分类"), []).append(p)

    if not topic_to_papers:
        lines.append("无。")
    else:
        for topic_name, items in topic_to_papers.items():
            lines.append(f"### {topic_name}")
            lines.append("")
            for p in items[:10]:
                lines.append(f"- **{p.get('priority_label')}｜{p.get('score')}分** [{p.get('title')}]({p.get('url')})")
            lines.append("")

    lines.append("## 四、适合科室分享的方向")
    lines.append("")
    lines.append("1. 老年或精神症状首发患者，需要持续关注痴呆、谵妄、自身免疫性脑炎、癫痫、代谢性脑病等器质性病因。")
    lines.append("2. 痴呆患者的幻觉、妄想、激越、淡漠、抑郁和睡眠障碍，是精神科专科医院神经内科的重要交叉管理方向。")
    lines.append("3. 抗精神病药、抗抑郁药、锂盐、丙戊酸等药物相关运动障碍、认知影响和癫痫风险，值得形成固定会诊思路。")
    lines.append("")

    return "\n".join(lines)


def save_report(markdown: str) -> Path:
    Path("reports").mkdir(exist_ok=True)
    today = date.today().isoformat()
    report_path = Path("reports") / f"{today}_weekly_report.md"
    latest_path = Path("reports") / "latest_report.md"
    report_path.write_text(markdown, encoding="utf-8")
    latest_path.write_text(markdown, encoding="utf-8")
    return report_path


def main():
    config = load_config()
    papers = collect_papers()
    data_path = save_papers(papers)
    report = make_report(papers, config)
    report_path = save_report(report)

    print(f"Saved data: {data_path}")
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
