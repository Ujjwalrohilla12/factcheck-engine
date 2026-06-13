"""OpenAI-powered LLM operations."""

from __future__ import annotations

import logging
import os
from typing import Any

from openai import APIError, OpenAI, RateLimitError

from utils.constants import (
    CLAIM_EXTRACTION_SYSTEM_PROMPT,
    CLAIM_EXTRACTION_TEMPERATURE,
    CLAIM_EXTRACTION_USER_PROMPT_PREFIX,
    ERROR_API_KEY,
    LLM_TEMPERATURE,
    VALID_STATUSES,
    VERIFICATION_SYSTEM_PROMPT,
    STATUS_UNVERIFIABLE,
    get_default_model,
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

        self.client = OpenAI(api_key=api_key, timeout=60, max_retries=0)
        self.model = model or get_default_model()

    def extract_claims(self, text: str) -> tuple[list[dict[str, str]], str | None]:
        """Extract factual claims as structured JSON."""
        try:
            safe_text = text[:12000]
            user_prompt = CLAIM_EXTRACTION_USER_PROMPT_PREFIX + safe_text
            response_text = self._json_chat(
                system_prompt=CLAIM_EXTRACTION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=CLAIM_EXTRACTION_TEMPERATURE,
                max_tokens=2500,
            )
            payload = extract_json_from_text(response_text, {"claims": []})
            if not isinstance(payload, dict):
                return [], "OpenAI returned an unexpected response format."
            raw_claims = payload.get("claims") or []
            if not isinstance(raw_claims, list):
                raw_claims = []
            valid_claims = []
            for item in raw_claims:
                if not isinstance(item, dict):
                    continue
                claim_text = str(item.get("claim") or "").strip()
                if not claim_text:
                    continue
                valid_claims.append({
                    "claim": claim_text,
                    "type": str(item.get("type") or "Other").strip(),
                })
            return valid_claims, None
        except RateLimitError:
            return [], "OpenAI rate limit reached. Please try again later."
        except APIError as exc:
            return [], f"OpenAI API error: {exc}"
        except Exception as exc:
            logger.exception("Unexpected error during claim extraction")
            return [], f"Claim extraction failed: {type(exc).__name__}: {exc}"

    def verify_claim(self, claim: str, evidence: str) -> tuple[dict[str, Any], str | None]:
        """Verify one claim against web evidence."""
        try:
            user_prompt = (
                "Claim:\n" + claim
                + "\n\nEvidence:\n" + evidence[:9000]
                + '\n\nReturn JSON: {"status": "Verified", "confidence": 90,'
                ' "explanation": "reason", "key_finding": "key fact"}'
            )
            response_text = self._json_chat(
                system_prompt=VERIFICATION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=LLM_TEMPERATURE,
                max_tokens=900,
            )
            payload = extract_json_from_text(response_text, {})
            if not isinstance(payload, dict):
                return self.default_verification("Could not parse verification response."), None
            status = str(payload.get("status") or STATUS_UNVERIFIABLE).strip()
            if status not in VALID_STATUSES:
                status = STATUS_UNVERIFIABLE
            return {
                "status": status,
                "confidence": safe_int(payload.get("confidence"), default=0),
                "explanation": str(payload.get("explanation") or "").strip(),
                "key_finding": str(payload.get("key_finding") or "").strip(),
            }, None
        except RateLimitError:
            return self.default_verification("OpenAI rate limit reached."), None
        except APIError as exc:
            return self.default_verification(f"OpenAI API error: {exc}"), None
        except Exception as exc:
            logger.exception("Unexpected error during claim verification")
            return self.default_verification(f"Verification failed: {type(exc).__name__}: {exc}"), None

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
