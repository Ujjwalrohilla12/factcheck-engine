"""Claim verification workflow."""

from __future__ import annotations

import logging
from typing import Any, Callable

from services.llm_service import LLMService
from services.search_service import SearchService
from utils.constants import STATUS_UNVERIFIABLE

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int], None]


class Verifier:
    """Verify extracted claims against live web evidence."""

    def __init__(self, model: str | None = None):
        self.llm_service = LLMService(model=model)
        self.search_service = SearchService()

    def verify_claims(
        self,
        claims: list[dict[str, str]],
        progress_callback: ProgressCallback | None = None,
        min_confidence: int = 0,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Verify a list of claims."""
        if not claims:
            logger.warning("No claims to verify")
            return [], "No claims to verify."

        logger.info(f"Starting verification of {len(claims)} claims")
        results: list[dict[str, Any]] = []
        for index, claim_data in enumerate(claims, start=1):
            if progress_callback:
                progress_callback(index - 1, len(claims))
            logger.debug(f"Verifying claim {index}/{len(claims)}: {claim_data.get('claim', '')[:50]}...")
            result = self.verify_single_claim(claim_data)
            if result.get("confidence", 0) >= min_confidence:
                results.append(result)
                logger.debug(f"Claim {index} passed confidence threshold ({result.get('confidence')}% >= {min_confidence}%)")
            else:
                logger.debug(f"Claim {index} filtered out (confidence {result.get('confidence')}% < {min_confidence}%)")

        if progress_callback:
            progress_callback(len(claims), len(claims))

        logger.info(f"Verification complete: {len(results)} claims passed filters")
        return results, None

    def verify_single_claim(self, claim_data: dict[str, str]) -> dict[str, Any]:
        """Verify one claim and attach evidence sources."""
        claim = claim_data.get("claim", "").strip()
        claim_type = claim_data.get("type", "Other")
        logger.debug(f"verify_single_claim called for: {claim[:60]}...")

        base_result: dict[str, Any] = {
            "claim": claim,
            "type": claim_type,
            "status": STATUS_UNVERIFIABLE,
            "confidence": 0,
            "explanation": "Unable to verify this claim.",
            "key_finding": "",
            "sources": [],
            "search_query": f"Verify claim: {claim}",
            "evidence_snippet": "",
        }

        logger.debug(f"Searching for evidence...")
        evidence_bundle, search_error = self.search_service.search_claim(claim)
        base_result["search_query"] = evidence_bundle.get("query", base_result["search_query"])
        base_result["sources"] = evidence_bundle.get("sources", [])
        base_result["evidence_snippet"] = evidence_bundle.get("evidence", "")[:1200]

        if search_error:
            logger.warning(f"Search error: {search_error}")
            base_result["explanation"] = f"Search failed: {search_error}"
            return base_result

        evidence = evidence_bundle.get("evidence", "")
        if not evidence:
            logger.warning(f"No evidence found for claim")
            base_result["explanation"] = "No relevant web evidence was found."
            return base_result

        logger.debug(f"Evidence found ({len(evidence)} chars), calling LLM for verification...")
        verification, verify_error = self.llm_service.verify_claim(claim, evidence)
        if verify_error:
            logger.warning(f"Verification error: {verify_error}")
            base_result["explanation"] = verify_error
            return base_result

        logger.debug(f"Verification complete: status={verification.get('status')}, confidence={verification.get('confidence')}%")
        base_result.update(verification)
        return base_result
