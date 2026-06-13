"""Demo session data matching the FactCheck AI presentation."""

from __future__ import annotations

from typing import Any

DEMO_DOCUMENT_NAME = "sample_marketing_report.pdf"
DEMO_METADATA = {"pages": 12, "file_size_mb": 1.8, "title": DEMO_DOCUMENT_NAME}

DEMO_CLAIMS: list[dict[str, str]] = [
    {"claim": "The global AI market will reach $1.8 trillion by 2030.", "type": "Market Statistic"},
    {"claim": "ChatGPT reached 200 million users as of 2024.", "type": "User Count"},
    {"claim": "Google holds 85% of the global search market in 2025.", "type": "Market Statistic"},
    {"claim": "Enterprise AI spending grew 38% year-over-year in 2024.", "type": "Growth Rate"},
    {"claim": "OpenAI reported $4.2 billion in annualized revenue in 2024.", "type": "Revenue"},
    {"claim": "GPT-4 was launched in March 2023.", "type": "Date"},
    {"claim": "Cloud infrastructure market share for AWS is 31% in 2024.", "type": "Percentage"},
    {"claim": "Cybersecurity breaches increased 72% between 2022 and 2024.", "type": "Percentage"},
]

DEMO_RESULTS: list[dict[str, Any]] = [
    {
        "claim": "The global AI market will reach $1.8 trillion by 2030.",
        "type": "Market Statistic",
        "status": "Verified",
        "confidence": 94,
        "explanation": "Multiple analyst forecasts place the AI market near $1.8T by 2030.",
        "key_finding": "Industry reports support a high-growth trajectory toward $1.8T.",
        "sources": [
            {"title": "Grand View Research", "url": "https://www.grandviewresearch.com/"},
            {"title": "MarketsandMarkets", "url": "https://www.marketsandmarkets.com/"},
        ],
        "search_query": 'market size statistic "The global AI market will reach $1.8 trillion by 2030." latest data',
        "evidence_snippet": "Analyst projections estimate the AI market could exceed $1.8 trillion by 2030.",
        "needs_review": False,
        "review_reason": "",
    },
    {
        "claim": "ChatGPT reached 200 million users as of 2024.",
        "type": "User Count",
        "status": "Inaccurate",
        "confidence": 71,
        "explanation": "Public reporting suggests weekly active users were lower than 200M in 2024.",
        "key_finding": "User counts vary by metric; 200M is higher than commonly cited weekly figures.",
        "sources": [
            {"title": "Reuters", "url": "https://www.reuters.com/"},
        ],
        "search_query": 'user count active users "ChatGPT reached 200 million users as of 2024." official',
        "evidence_snippet": "Coverage in 2024 cited strong adoption but mixed definitions of active users.",
        "needs_review": True,
        "review_reason": "Confidence 71% is below the 60% review threshold.",
    },
    {
        "claim": "Google holds 85% of the global search market in 2025.",
        "type": "Market Statistic",
        "status": "False",
        "confidence": 88,
        "explanation": "Recent market share estimates place Google below 85% globally.",
        "key_finding": "StatCounter and similar trackers show search share closer to the low 90s in some regions but not uniformly 85% globally.",
        "sources": [
            {"title": "StatCounter", "url": "https://gs.statcounter.com/"},
        ],
        "search_query": 'market size statistic "Google holds 85% of the global search market in 2025." latest data',
        "evidence_snippet": "Search share varies by region and metric; 85% is not consistently supported.",
        "needs_review": False,
        "review_reason": "",
    },
    {
        "claim": "Enterprise AI spending grew 38% year-over-year in 2024.",
        "type": "Growth Rate",
        "status": "Verified",
        "confidence": 82,
        "explanation": "Enterprise AI investment reports show strong double-digit growth in 2024.",
        "key_finding": "Multiple surveys cite growth above 30% for enterprise AI budgets.",
        "sources": [{"title": "IDC", "url": "https://www.idc.com/"}],
        "search_query": 'growth rate percentage "Enterprise AI spending grew 38% year-over-year in 2024." verified',
        "evidence_snippet": "Industry surveys report rapid enterprise AI budget expansion in 2024.",
        "needs_review": False,
        "review_reason": "",
    },
    {
        "claim": "OpenAI reported $4.2 billion in annualized revenue in 2024.",
        "type": "Revenue",
        "status": "Inaccurate",
        "confidence": 76,
        "explanation": "Revenue figures reported in 2024 differ depending on the reporting period and source.",
        "key_finding": "$4.2B annualized revenue appears in some reports but is not universally confirmed.",
        "sources": [{"title": "The Information", "url": "https://www.theinformation.com/"}],
        "search_query": 'company revenue earnings "OpenAI reported $4.2 billion in annualized revenue in 2024." official filing',
        "evidence_snippet": "Media coverage referenced strong revenue growth but with varying exact figures.",
        "needs_review": True,
        "review_reason": "Confidence 76% is below the 60% review threshold.",
    },
    {
        "claim": "GPT-4 was launched in March 2023.",
        "type": "Date",
        "status": "Verified",
        "confidence": 98,
        "explanation": "OpenAI announced GPT-4 on March 14, 2023.",
        "key_finding": "Launch date is widely documented by OpenAI and major news outlets.",
        "sources": [{"title": "OpenAI", "url": "https://openai.com/"}],
        "search_query": 'event date timeline "GPT-4 was launched in March 2023." confirmed',
        "evidence_snippet": "OpenAI published the GPT-4 release in March 2023.",
        "needs_review": False,
        "review_reason": "",
    },
    {
        "claim": "Cloud infrastructure market share for AWS is 31% in 2024.",
        "type": "Percentage",
        "status": "Verified",
        "confidence": 91,
        "explanation": "Analyst estimates for AWS cloud share in 2024 are close to 31%.",
        "key_finding": "Synergy Research and similar firms place AWS near 31% share.",
        "sources": [{"title": "Synergy Research", "url": "https://www.srgresearch.com/"}],
        "search_query": 'percentage statistic "Cloud infrastructure market share for AWS is 31% in 2024." credible source',
        "evidence_snippet": "Market share trackers place AWS around 30-32% in 2024.",
        "needs_review": False,
        "review_reason": "",
    },
    {
        "claim": "Cybersecurity breaches increased 72% between 2022 and 2024.",
        "type": "Percentage",
        "status": "Unverifiable",
        "confidence": 52,
        "explanation": "Available public sources do not consistently support a precise 72% increase.",
        "key_finding": "Breach statistics vary widely by dataset and definition.",
        "sources": [],
        "search_query": 'percentage statistic "Cybersecurity breaches increased 72% between 2022 and 2024." credible source',
        "evidence_snippet": "Security reports show rising incidents but not a uniform 72% figure.",
        "needs_review": True,
        "review_reason": "Confidence 52% is below the 60% review threshold.",
    },
]


def load_demo_session(session_state) -> None:
    """Populate Streamlit session state with presentation demo data."""
    session_state.extracted_text = "Demo marketing report loaded from sample session."
    session_state.extracted_claims = DEMO_CLAIMS
    session_state.verification_results = DEMO_RESULTS
    session_state.document_name = DEMO_DOCUMENT_NAME
    session_state.document_metadata = DEMO_METADATA
    session_state.workflow_step = 8
    session_state.demo_mode = True
