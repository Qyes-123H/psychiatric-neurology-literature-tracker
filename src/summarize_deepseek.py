import os
from pathlib import Path
from typing import Dict, Any

import requests
import yaml


def load_prompt(prompt_path: str = "prompts/paper_summary.md") -> str:
    return Path(prompt_path).read_text(encoding="utf-8")


def load_config(config_path: str = "config/topics.yml") -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def summarize_paper_with_deepseek(paper: Dict[str, Any], config: Dict[str, Any]) -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return "未配置 DEEPSEEK_API_KEY，已跳过 AI 总结。"

    ai_settings = config.get("ai_settings", {})
    model = os.getenv("DEEPSEEK_MODEL", ai_settings.get("model", "deepseek-v4-flash"))

    system_prompt = load_prompt()
    topic_names = "、".join([t.get("name", "") for t in paper.get("topics", [])])

    user_prompt = f"""
请总结以下 PubMed 文献：

题目：{paper.get("title", "")}

期刊：{paper.get("journal", "")}

发表日期：{paper.get("pub_date", "")}

PMID：{paper.get("pmid", "")}

所属追踪主题：{topic_names}

摘要：
{paper.get("abstract", "")[:4000]}
"""

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": ai_settings.get("temperature", 0.2),
        "max_tokens": ai_settings.get("max_tokens", 1200),
        "thinking": {"type": "disabled"},
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers=headers,
        json=payload,
        timeout=90,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()
