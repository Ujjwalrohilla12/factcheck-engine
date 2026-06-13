"""Shared utility functions."""

from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from typing import Any

from utils.constants import (
    ERROR_FILE_SIZE,
    ERROR_FILE_TYPE,
    MAX_PDF_SIZE_BYTES,
    STATUS_FALSE,
    STATUS_INACCURATE,
    STATUS_UNVERIFIABLE,
    STATUS_VERIFIED,
)


def validate_pdf_file(uploaded_file) -> tuple[bool, str | None]:
    """Validate a Streamlit uploaded PDF."""
    if uploaded_file is None:
        return False, "No file provided."

    file_type = getattr(uploaded_file, "type", "")
    file_name = getattr(uploaded_file, "name", "")

    if file_type != "application/pdf" and not file_name.lower().endswith(".pdf"):
        return False, ERROR_FILE_TYPE

    if getattr(uploaded_file, "size", 0) > MAX_PDF_SIZE_BYTES:
        return False, ERROR_FILE_SIZE

    return True, None


def sanitize_text(text: str) -> str:
    """Normalize extracted text while preserving sentence boundaries."""
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_json_from_text(text: str, default: Any) -> Any:
    """Parse JSON from an LLM response, allowing accidental code fences."""
    if not text:
        return default

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"(\{.*\}|\[.*\])", cleaned, flags=re.DOTALL)
    if not match:
        return default

    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return default


def clean_claim_text(claim: str) -> str:
    """Clean a claim for display and deduplication."""
    claim = re.sub(r"\s+", " ", claim).strip(" -:\t\r\n")
    if claim and claim[-1] not in ".!?":
        claim += "."
    return claim


def remove_duplicate_claims(claims: list[dict[str, Any]], threshold: float = 0.92) -> list[dict[str, Any]]:
    """Remove exact and near-duplicate claims."""
    unique: list[dict[str, Any]] = []
    normalized_seen: list[str] = []

    for claim_data in claims:
        claim = clean_claim_text(str(claim_data.get("claim", "")))
        normalized = re.sub(r"[^a-z0-9]+", " ", claim.lower()).strip()
        if not normalized:
            continue

        is_duplicate = any(
            normalized == existing
            or SequenceMatcher(None, normalized, existing).ratio() >= threshold
            for existing in normalized_seen
        )
        if not is_duplicate:
            copied = dict(claim_data)
            copied["claim"] = claim
            unique.append(copied)
            normalized_seen.append(normalized)

    return unique


def calculate_claim_statistics(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Return aggregate counts and confidence metrics."""
    total = len(results)
    confidence_values = [int(r.get("confidence", 0)) for r in results]

    return {
        "total": total,
        "verified": sum(1 for r in results if r.get("status") == STATUS_VERIFIED),
        "inaccurate": sum(1 for r in results if r.get("status") == STATUS_INACCURATE),
        "false": sum(1 for r in results if r.get("status") == STATUS_FALSE),
        "unverifiable": sum(1 for r in results if r.get("status") == STATUS_UNVERIFIABLE),
        "avg_confidence": round(sum(confidence_values) / total) if total else 0,
    }


def safe_int(value: Any, default: int = 0, lower: int = 0, upper: int = 100) -> int:
    """Coerce a value into a bounded integer."""
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(lower, min(upper, number))


def truncate_text(text: str, max_length: int = 220) -> str:
    """Truncate long UI text."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."
