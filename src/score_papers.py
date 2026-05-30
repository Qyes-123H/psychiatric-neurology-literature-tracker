HIGH_VALUE_TERMS = [
    "dementia",
    "alzheimer",
    "parkinson",
    "lewy body",
    "frontotemporal",
    "mild cognitive impairment",
    "psychosis",
    "hallucination",
    "delusion",
    "agitation",
    "depression",
    "anxiety",
    "apathy",
    "sleep disorder",
    "autoimmune encephalitis",
    "delirium",
    "epilepsy",
    "seizure",
    "drug-induced parkinsonism",
    "tardive dyskinesia",
    "neuroleptic malignant syndrome",
    "serotonin syndrome",
    "biomarker",
    "mri",
    "pet",
    "neurofilament light",
    "gfap",
    "tau",
    "amyloid",
    "alpha-synuclein",
]

CLINICAL_STUDY_TERMS = [
    "cohort",
    "randomized",
    "clinical trial",
    "meta-analysis",
    "systematic review",
    "guideline",
    "consensus",
    "case report",
    "case series",
    "diagnostic criteria",
]

LOW_VALUE_TERMS = [
    "zebrafish",
    "drosophila",
    "cell line",
    "molecular docking",
]


def score_paper(title: str, abstract: str = "", topic_priority: int = 3) -> int:
    text = f"{title or ''} {abstract or ''}".lower()
    score = topic_priority

    for term in HIGH_VALUE_TERMS:
        if term in text:
            score += 3

    for term in CLINICAL_STUDY_TERMS:
        if term in text:
            score += 2

    for term in LOW_VALUE_TERMS:
        if term in text:
            score -= 4

    return score


def classify_priority(score: int) -> str:
    if score >= 16:
        return "必读"
    if score >= 10:
        return "建议阅读"
    if score >= 5:
        return "可浏览"
    return "低优先级"
