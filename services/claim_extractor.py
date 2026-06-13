"""Claim extraction orchestration."""

from __future__ import annotations

import logging

from services.llm_service import LLMService
from utils.constants import CLAIM_TYPES
from utils.helpers import clean_claim_text, remove_duplicate_claims

logger = logging.getLogger(__name__)


class ClaimExtractor:
    """Extract, clean, and deduplicate factual claims."""

    def __init__(self, model: str | None = None):
        self.llm_service = LLMService(model=model)

    def extract_and_process_claims(
        self,
        text: str,
        remove_duplicates: bool = True,
        max_claims: int = 100,
    ) -> tuple[list[dict[str, str]], str | None]:
        """Extract factual claims from long document text."""
        if not text or len(text.strip()) < 100:
            logger.warning("Text is too short to extract meaningful claims")
            return [], "Text is too short to extract meaningful claims."

        logger.info(f"Starting claim extraction from {len(text)} characters")
        all_claims: list[dict[str, str]] = []
        errors: list[str] = []

        chunks = self._chunk_text(text)
        logger.debug(f"Text split into {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks, start=1):
            logger.debug(f"Processing chunk {i}/{len(chunks)}...")
            claims, error = self.llm_service.extract_claims(chunk)
            if error:
                logger.warning(f"Error extracting claims from chunk {i}: {error}")
                errors.append(error)
            else:
                logger.debug(f"Extracted {len(claims)} claims from chunk {i}")
            all_claims.extend(claims)

        logger.info(f"Total claims extracted: {len(all_claims)}")
        
        cleaned = self._validate_and_clean_claims(all_claims)
        logger.info(f"After cleaning: {len(cleaned)} claims")
        
        if remove_duplicates:
            logger.debug("Removing duplicate claims...")
            cleaned = remove_duplicate_claims(cleaned)
            logger.info(f"After deduplication: {len(cleaned)} claims")

        if not cleaned and errors:
            error_msg = "; ".join(sorted(set(errors)))
            logger.error(f"No claims extracted. Errors: {error_msg}")
            return [], error_msg

        result = cleaned[:max_claims]
        logger.info(f"Returning {len(result)} claims (max {max_claims})")
        return result, None

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 10000, overlap: int = 600) -> list[str]:
        """Split text into overlapping character chunks."""
        chunks: list[str] = []
        start = 0
        text = text.strip()

        while start < len(text) and len(chunks) < 8:
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)
            if end == len(text):
                break
            start = max(0, end - overlap)

        return chunks

    @staticmethod
    def _validate_and_clean_claims(claims: list[dict[str, str]]) -> list[dict[str, str]]:
        cleaned: list[dict[str, str]] = []
        for claim_data in claims:
            claim = clean_claim_text(str(claim_data.get("claim", "")))
            claim_type = str(claim_data.get("type", "Other")).strip()

            if len(claim) < 12:
                continue
            if len(claim) > 600:
                claim = claim[:597].rstrip() + "..."
            if claim_type not in CLAIM_TYPES:
                claim_type = "Other"

            cleaned.append({"claim": claim, "type": claim_type})

        return cleaned
