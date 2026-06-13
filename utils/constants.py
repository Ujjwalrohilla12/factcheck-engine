"""Application constants for FactCheck AI."""

from __future__ import annotations

import os

APP_NAME = "FactCheck AI"
MAX_PDF_SIZE_MB = 25
MAX_PDF_SIZE_BYTES = MAX_PDF_SIZE_MB * 1024 * 1024

SEARCH_RESULTS_COUNT = int(os.getenv("SEARCH_RESULTS_COUNT", "5"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))

DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
SUPPORTED_MODELS = ["gpt-4o-mini", "gpt-4.1", "gpt-4o"]
LLM_TEMPERATURE = 0.2
CLAIM_EXTRACTION_TEMPERATURE = 0.1

STATUS_VERIFIED = "Verified"
STATUS_INACCURATE = "Inaccurate"
STATUS_FALSE = "False"
STATUS_UNVERIFIABLE = "Unverifiable"
VALID_STATUSES = [
    STATUS_VERIFIED,
    STATUS_INACCURATE,
    STATUS_FALSE,
    STATUS_UNVERIFIABLE,
]

STATUS_COLORS = {
    STATUS_VERIFIED: "#16a34a",
    STATUS_INACCURATE: "#ca8a04",
    STATUS_FALSE: "#dc2626",
    STATUS_UNVERIFIABLE: "#64748b",
}

STATUS_LABELS = {
    STATUS_VERIFIED: "Verified",
    STATUS_INACCURATE: "Inaccurate",
    STATUS_FALSE: "False",
    STATUS_UNVERIFIABLE: "Unverifiable",
}

CLAIM_TYPES = [
    "Market Statistic",
    "Financial Number",
    "User Count",
    "Growth Rate",
    "Date",
    "Technical Figure",
    "Technical Specification",
    "Revenue",
    "Percentage",
    "Other",
]

ERROR_FILE_SIZE = f"File size exceeds the {MAX_PDF_SIZE_MB} MB limit."
ERROR_FILE_TYPE = "Please upload a valid PDF file."
ERROR_INVALID_PDF = "No extractable text was found. Scanned PDFs need OCR before upload."
ERROR_API_KEY = "Missing API configuration. Set OPENAI_API_KEY and TAVILY_API_KEY."

CLAIM_EXTRACTION_SYSTEM_PROMPT = """You extract factual claims from documents.
Return only claims that can be checked against external evidence. Focus on dates,
percentages, statistics, revenue, financial numbers, market figures, growth rates,
technical figures, and user counts. Do not include opinions or vague marketing copy."""

CLAIM_EXTRACTION_USER_PROMPT = """Extract factual claims from this text.

Return JSON with this exact shape:
{"claims":[{"claim":"AI market size was $196 billion in 2024","type":"Market Statistic"}]}

Allowed type values:
Market Statistic, Financial Number, User Count, Growth Rate, Date,
Technical Figure, Technical Specification, Revenue, Percentage, Other

Text:
{text}"""

VERIFICATION_SYSTEM_PROMPT = """You are a careful fact-checking analyst.
Compare the claim against the supplied web evidence. Classify only as:
Verified, Inaccurate, False, or Unverifiable.

Verified means credible evidence directly matches the claim.
Inaccurate means the claim is partly correct but materially outdated, incomplete, or modified.
False means credible evidence contradicts the claim or no credible evidence supports a specific assertion.
Unverifiable means the provided evidence is insufficient."""

VERIFICATION_USER_PROMPT = """Claim:
{claim}

Evidence:
{evidence}

Return JSON with this exact shape:
{{
  "status": "Verified",
  "confidence": 90,
  "explanation": "Brief reason grounded in the sources.",
  "key_finding": "Most important supporting or contradicting fact."
}}"""
