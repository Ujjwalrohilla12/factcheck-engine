"""OpenAI-powered LLM operations."""

from __future__ import annotations

import logging
import os
from typing import Any

from openai import APIError, OpenAI, RateLimitError

from utils.constants import (
    CLAIM_EXTRACTION_SYSTEM_PROMPT,
    CLAIM_EXTRACTION_TEMPERATURE,
    CLAIM_EXTRACTION_USER_PROMPT,
    DEFAULT_MODEL,
    ERROR_API_KEY,
    LLM_TEMPERATURE,
    VALID_STATUSES,
    VERIFICATION_SYSTEM_PROMPT,
    VERIFICATION_USER_PROMPT,
    STATUS_UNVERIFIABLE,
)
from utils.helpers import extract_json_from_text, safe_int
from utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class LLMService:
    """Thin service wrapper around OpenAI Chat Completions."""

    def __init__(self, model: str | None = None):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(ERROR_API_KEY)

        self.client = OpenAI(api_key=api_key, timeout=60, max_retries=2)
        self.model = model or DEFAULT_MODEL

    def extract_claims(self, text: str) -> tuple[list[dict[str, str]], str | None]:
        """Extract factual claims as structured JSON."""
        try:
            logger.debug(f"Extracting claims from {len(text)} characters of text")
            response_text = self._json_chat(
                system_prompt=CLAIM_EXTRACTION_SYSTEM_PROMPT,
                user_prompt=CLAIM_EXTRACTION_USER_PROMPT.format(text=text[:12000]),
                temperature=CLAIM_EXTRACTION_TEMPERATURE,
                max_tokens=2500,
            )
            logger.debug(f"OpenAI response (first 200 chars): {response_text[:200]}")
            
            payload = extract_json_from_text(response_text, {"claims": []})
            logger.debug(f"Parsed payload type: {type(payload)}, keys: {payload.keys() if isinstance(payload, dict) else 'N/A'}")
            
            # Defensive check: ensure payload is a dictionary
            if not isinstance(payload, dict):
                logger.error(f"Payload is not a dict, it's a {type(payload).__name__}")
                return [], "OpenAI returned an invalid claims payload (not a dictionary)."
            
            # Extract claims array with fallback
            claims = payload.get("claims")
            if claims is None:
                logger.warning("'claims' key not found in payload, using empty list")
                claims = []
            
            # Ensure claims is a list
            if not isinstance(claims, list):
                logger.error(f"Claims is not a list, it's a {type(claims).__name__}: {claims}")
                return [], f"OpenAI returned invalid claims (expected list, got {type(claims).__name__})."
            
            logger.info(f"Successfully parsed {len(claims)} claims from response")
            
            # Process and validate each claim
            valid_claims = []
            for i, item in enumerate(claims):
                if not isinstance(item, dict):
                    logger.warning(f"Claim {i} is not a dict: {type(item).__name__}")
                    continue
                claim_text = str(item.get("claim", "")).strip()
                if not claim_text:
                    logger.debug(f"Skipping claim {i}: empty claim text")
                    continue
                claim_type = str(item.get("type", "Other")).strip()
                valid_claims.append({"claim": claim_text, "type": claim_type})
            
            logger.info(f"Extracted {len(valid_claims)} valid claims")
            return valid_claims, None
        except RateLimitError:
            logger.error("OpenAI rate limit reached")
            return [], "OpenAI rate limit reached. Please try again later."
        except APIError as exc:
            logger.error(f"OpenAI API error: {exc}")
            return [], f"OpenAI API error: {exc}"
        except Exception as exc:
            logger.exception(f"Unexpected error during claim extraction: {exc}")
            return [], f"Claim extraction error: {exc}"

    def verify_claim(self, claim: str, evidence: str) -> tuple[dict[str, Any], str | None]:
        """Verify one claim against web evidence."""
        try:
            logger.debug(f"Verifying claim: {claim[:80]}...")
            response_text = self._json_chat(
                system_prompt=VERIFICATION_SYSTEM_PROMPT,
                user_prompt=VERIFICATION_USER_PROMPT.format(
                    claim=claim,
                    evidence=evidence[:9000],
                ),
                temperature=LLM_TEMPERATURE,
                max_tokens=900,
            )
            logger.debug(f"Verification response (first 200 chars): {response_text[:200]}")
            
            payload = extract_json_from_text(response_text, {})
            logger.debug(f"Parsed verification payload type: {type(payload)}, keys: {payload.keys() if isinstance(payload, dict) else 'N/A'}")
            
            if not isinstance(payload, dict):
                logger.error(f"Verification payload is not a dict: {type(payload).__name__}")
                return self.default_verification("Could not parse verification JSON (not a dictionary)."), None

            status = str(payload.get("status", STATUS_UNVERIFIABLE)).strip()
            if status not in VALID_STATUSES:
                logger.warning(f"Invalid status '{status}', defaulting to {STATUS_UNVERIFIABLE}")
                status = STATUS_UNVERIFIABLE

            result = {
                "status": status,
                "confidence": safe_int(payload.get("confidence"), default=0),
                "explanation": str(payload.get("explanation", "")).strip(),
                "key_finding": str(payload.get("key_finding", "")).strip(),
            }
            logger.debug(f"Verification result: status={status}, confidence={result['confidence']}%")
            return result, None
        except RateLimitError:
            logger.error("OpenAI rate limit reached during verification")
            return self.default_verification("OpenAI rate limit reached."), None
        except APIError as exc:
            logger.error(f"OpenAI API error during verification: {exc}")
            return self.default_verification(f"OpenAI API error: {exc}"), None
        except Exception as exc:
            logger.exception(f"Unexpected error during claim verification: {exc}")
            return self.default_verification(f"Verification error: {exc}"), None

    def _json_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Call Chat Completions in JSON-object mode."""

        def _call() -> str:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content or "{}"

        return retry_with_backoff(
            _call,
            max_attempts=3,
            base_delay=1.5,
            retry_exceptions=(RateLimitError, APIError),
        )

    @staticmethod
    def default_verification(explanation: str) -> dict[str, Any]:
        return {
            "status": STATUS_UNVERIFIABLE,
            "confidence": 0,
            "explanation": explanation,
            "key_finding": "",
        }
