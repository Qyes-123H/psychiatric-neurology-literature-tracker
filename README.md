# Psychiatric-Neurology Literature Tracker
精神科专科医院神经内科文献追踪系统

这个项目用于每周自动追踪 PubMed 最新文献，并按“精神科专科医院中的神经内科工作场景”进行整理与总结。

## 适用场景

你即将在精神科专科医院的神经内科工作，患者常见特点包括：

- 神经退行性疾病：AD、PD、DLB、FTD、PSP、MSA、ALS、MCI
- 精神症状共病：焦虑、抑郁、幻觉、妄想、激越、淡漠、睡眠障碍
- 精神症状背后的器质性病因：自身免疫性脑炎、癫痫、谵妄、脑肿瘤、代谢性脑病、神经梅毒、HIV、Wilson病、朊蛋白病
- 精神科药物相关神经系统问题：药源性帕金森、迟发性运动障碍、急性肌张力障碍、静坐不能、恶性综合征、5-HT综合征等

## 项目结构

```text
.
├── .github/workflows/weekly-literature-tracker.yml
├── config/topics.yml
├── prompts/paper_summary.md
├── src/
│   ├── fetch_pubmed.py
│   ├── score_papers.py
│   ├── summarize_deepseek.py
│   └── generate_report.py
├── data/
├── reports/
├── requirements.txt
└── README.md
```

## GitHub Secrets

请在 GitHub 仓库中设置以下 Secrets：

| Secret 名称 | 是否必需 | 说明 |
|---|---:|---|
| `NCBI_EMAIL` | 推荐 | 你的邮箱，用于 NCBI E-utilities 请求标识 |
| `NCBI_API_KEY` | 可选 | NCBI API key；请求量不大时可以不填 |
| `DEEPSEEK_API_KEY` | 可选 | 填写后会自动生成 AI 中文临床总结 |

## 手动运行

GitHub 网页端进入：

`Actions` → `Weekly Psychiatric-Neurology Literature Tracker` → `Run workflow`

## 周报位置

运行完成后，查看：

- `reports/latest_report.md`
- `reports/YYYY-MM-DD_weekly_report.md`

## 修改追踪方向

主要修改：

```text
config/topics.yml
```

每个 topic 包括：

- `id`
- `name`
- `priority`
- `query`

## 本地运行

```bash
pip install -r requirements.txt
python src/generate_report.py
```

如果你没有 DeepSeek API key，程序仍然会生成基础版周报。
