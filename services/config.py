"""Centralized configuration — loads all secrets from environment.

Priority order:
  1. Streamlit Cloud secrets  (production)
  2. .env file                (local development)
  3. System environment       (CI / Docker)

No API keys are ever exposed to the frontend.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# ── Load .env first (no-op if file is absent) ─────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)   # don't overwrite values already in os.environ
except Exception:
    pass

# ── Pull from Streamlit secrets if available ──────────────────────────────────
_KEYS = (
    "OPENAI_API_KEY",
    "TAVILY_API_KEY",
    "LLM_MODEL",
    "SEARCH_RESULTS_COUNT",
    "REQUEST_TIMEOUT_SECONDS",
)

def _load_streamlit_secrets() -> None:
    """Copy Streamlit secrets into os.environ (only if not already set)."""
    try:
        import streamlit as st
        secrets = st.secrets
        for key in _KEYS:
            if os.environ.get(key, "").strip():
                continue                          # already present — skip
            value: str | None = None
            try:
                if key in secrets:
                    value = str(secrets[key]).strip() or None
                elif "general" in secrets and key in secrets["general"]:
                    value = str(secrets["general"][key]).strip() or None
            except Exception:
                continue
            if value:
                os.environ[key] = value
    except Exception:
        pass   # Streamlit not initialised yet, or no secrets file — fine

_load_streamlit_secrets()

# ── Public constants (resolved once at import time) ───────────────────────────
OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
TAVILY_API_KEY: str = os.environ.get("TAVILY_API_KEY", "")
LLM_MODEL: str      = os.environ.get("LLM_MODEL", "gpt-4o-mini")

try:
    SEARCH_RESULTS_COUNT: int = int(os.environ.get("SEARCH_RESULTS_COUNT", "5"))
except ValueError:
    SEARCH_RESULTS_COUNT = 5

try:
    REQUEST_TIMEOUT_SECONDS: int = int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "30"))
except ValueError:
    REQUEST_TIMEOUT_SECONDS = 30

# ── Validation ────────────────────────────────────────────────────────────────
def validate_config() -> list[str]:
    """Return list of missing required keys (empty = all good)."""
    missing = []
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if not TAVILY_API_KEY:
        missing.append("TAVILY_API_KEY")
    return missing


def assert_config() -> None:
    """Raise ValueError if any required key is missing."""
    missing = validate_config()
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Set them in .env (local) or Streamlit Cloud Secrets (production)."
        )
