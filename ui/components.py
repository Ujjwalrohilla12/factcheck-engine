"""Reusable UI components aligned with the FactCheck AI presentation."""

from __future__ import annotations

from html import escape

import streamlit as st

from utils.constants import (
    STATUS_COLORS,
    STATUS_FALSE,
    STATUS_INACCURATE,
    STATUS_UNVERIFIABLE,
    STATUS_VERIFIED,
)
from utils.helpers import calculate_claim_statistics, truncate_text

WORKFLOW_STEPS = [
    "PDF Upload",
    "Text Extract",
    "Claim Detection",
    "Dedup + Classify",
    "Web Search",
    "AI Verdict",
    "Confidence Score",
    "Report Export",
]


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-wrap">
            <div class="hero-kicker">AI-POWERED</div>
            <div class="hero-title">FactCheck AI</div>
            <div class="hero-subtitle">Automated PDF Claim Verification System</div>
            <div class="hero-badges">
                <span class="badge verified">✓ VERIFIED</span>
                <span class="badge inaccurate">~ INACCURATE</span>
                <span class="badge false">✗ FALSE</span>
            </div>
            <div class="hero-footer">
                Built with GPT-4o-mini · LangChain · Tavily Search · Streamlit · PyMuPDF
                &nbsp;|&nbsp; CogCulture Assessment · June 2026
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard_header() -> None:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">🔍 FactCheck AI | Automated PDF Claim Verification</div>
            <p class="section-desc">Clean, intuitive Streamlit dashboard designed for non-technical users.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow(active_step: int) -> None:
    steps_html = ['<div class="workflow-grid">']
    for index, label in enumerate(WORKFLOW_STEPS, start=1):
        state_class = "done" if index < active_step else ("active" if index == active_step else "")
        steps_html.append(
            f'<div class="workflow-step {state_class}">'
            f'<div class="workflow-num">{index}</div>'
            f'<div class="workflow-label">{escape(label)}</div>'
            f"</div>"
        )
    steps_html.append("</div>")
    st.markdown("".join(steps_html), unsafe_allow_html=True)


def render_summary_panel(results: list[dict]) -> None:
    stats = calculate_claim_statistics(results) if results else {
        "total": 0,
        "verified": 0,
        "inaccurate": 0,
        "false": 0,
        "unverifiable": 0,
        "avg_confidence": 0,
    }
    claims_count = len(st.session_state.get("extracted_claims", []))
    total_display = stats["total"] if results else claims_count

    st.markdown(
        f"""
        <div class="section-card">
            <div class="section-title">📊 Summary</div>
            <div class="summary-grid">
                <div class="summary-tile total">
                    <div class="summary-label">Total Claims</div>
                    <div class="summary-value">{total_display}</div>
                </div>
                <div class="summary-tile verified">
                    <div class="summary-label">✓ Verified</div>
                    <div class="summary-value">{stats["verified"]}</div>
                </div>
                <div class="summary-tile inaccurate">
                    <div class="summary-label">~ Inaccurate</div>
                    <div class="summary-value">{stats["inaccurate"]}</div>
                </div>
                <div class="summary-tile false">
                    <div class="summary-label">✗ False</div>
                    <div class="summary-value">{stats["false"]}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _status_class(status: str) -> str:
    return {
        STATUS_VERIFIED: "verified",
        STATUS_INACCURATE: "inaccurate",
        STATUS_FALSE: "false",
    }.get(status, "unverifiable")


def _status_label(status: str) -> str:
    return {
        STATUS_VERIFIED: "✓ VERIFIED",
        STATUS_INACCURATE: "~ INACCURATE",
        STATUS_FALSE: "✗ FALSE",
        STATUS_UNVERIFIABLE: "? UNVERIFIABLE",
    }.get(status, status.upper())


def render_verification_results(results: list[dict], limit: int = 8) -> None:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Verification Results</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not results:
        st.info("Run verification to see colour-coded verdict cards here.")
        return

    for result in results[:limit]:
        status = result.get("status", STATUS_UNVERIFIABLE)
        css_class = _status_class(status)
        claim = escape(truncate_text(str(result.get("claim", "")), 180))
        confidence = result.get("confidence", 0)
        review_html = ""
        if result.get("needs_review"):
            review_html = (
                f'<span class="review-flag">Needs human review: '
                f'{escape(str(result.get("review_reason", "Low confidence")))}</span>'
            )

        st.markdown(
            f"""
            <div class="result-card {css_class}">
                <div class="result-status" style="color:{STATUS_COLORS.get(status, '#64748b')}">
                    {_status_label(status)}
                </div>
                <div class="result-claim">{claim}</div>
                <div class="result-meta">Confidence: {confidence}%</div>
                {review_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if len(results) > limit:
        st.caption(f"+ {len(results) - limit} more claims below in the detailed report tab.")


def render_solution_overview() -> None:
    st.markdown(
        """
        <div class="info-grid">
            <div class="info-tile"><h5>📄 PDF Intelligence</h5><p>Multi-page parsing with PyMuPDF + pdfplumber for text and tables.</p></div>
            <div class="info-tile"><h5>🔍 Claim Extraction</h5><p>GPT identifies stats, dates, percentages, revenue figures and growth rates.</p></div>
            <div class="info-tile"><h5>🌐 Live Verification</h5><p>Tavily Search fetches real-time web evidence instead of stale training data.</p></div>
            <div class="info-tile"><h5>🧠 AI Verdict Engine</h5><p>GPT-4o-mini compares claim vs evidence and assigns a confidence score.</p></div>
            <div class="info-tile"><h5>📊 Visual Dashboard</h5><p>Progress tracking, colour-coded verdicts, and expandable evidence panels.</p></div>
            <div class="info-tile"><h5>📥 Multi-format Export</h5><p>Download CSV, PDF, or Markdown reports for stakeholders.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_security_panel() -> None:
    items = [
        ("🔐 API Key Security", "Keys load from `.env` or Streamlit secrets and never appear in the UI."),
        ("🛡️ Input Validation", "PDF type checking, 50 MB size limits, and malformed file detection."),
        ("⚠️ Error Handling", "Graceful degradation when Tavily or OpenAI fail, with clear user messages."),
        ("⏱️ Rate Limiting", "Exponential backoff on API calls with progress updates during retries."),
        ("🔒 Data Privacy", "PDFs processed in memory only. Session data clears on refresh."),
        ("📊 Confidence Thresholds", "Low-confidence verdicts are flagged for human review."),
    ]
    cols = st.columns(3)
    for index, (title, body) in enumerate(items):
        with cols[index % 3]:
            st.markdown(
                f"""
                <div class="info-tile">
                    <h5>{escape(title)}</h5>
                    <p>{escape(body)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_architecture_panel() -> None:
    st.markdown(
        """
        ```text
        PRESENTATION LAYER          PROCESSING LAYER           INTELLIGENCE LAYER
        Streamlit Web UI      →     PDF Parser (PyMuPDF)  →    Tavily Search API
        File Upload                 Claim Extractor            GPT-4o-mini Engine
        Dashboard & Charts          Dedup Engine               Confidence Scorer
        Export Controls             Report Generator           Evidence Collector
        ```
        """
    )


def render_roadmap_panel() -> None:
    st.markdown(
        """
        **Phase 2 (Q3 2026):** Multi-document batch processing · Browser extension · Slack & Notion integration · Custom confidence thresholds

        **Phase 3 (Q4 2026):** Domain-specific models · Audit trail · White-label API · Multi-language support

        **Phase 4 (2027):** Real-time document monitoring · AI-assisted claim rewriting · CMS integrations · SOC2 compliance
        """
    )
