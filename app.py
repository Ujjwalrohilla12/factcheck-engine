"""FactCheck AI Streamlit application."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

# ── 1. Load .env for local dev (no-op on Streamlit Cloud) ────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ── 2. Inject Streamlit Cloud secrets into os.environ FIRST ──────────────────
#    Must happen before any import that calls os.getenv at module level.
def _load_streamlit_secrets() -> dict[str, bool]:
    """Copy every Streamlit secret into os.environ. Returns a status dict."""
    status: dict[str, bool] = {"openai": False, "tavily": False, "loaded": False}
    try:
        secrets = st.secrets          # raises FileNotFoundError if no secrets configured
        status["loaded"] = True
        _KEYS = (
            "OPENAI_API_KEY",
            "TAVILY_API_KEY",
            "LLM_MODEL",
            "SEARCH_RESULTS_COUNT",
            "REQUEST_TIMEOUT_SECONDS",
        )
        for key in _KEYS:
            # Accept both flat and nested [general] section
            value = None
            if key in secrets:
                value = str(secrets[key]).strip()
            elif hasattr(secrets, "general") and key in secrets.general:
                value = str(secrets.general[key]).strip()
            if value:
                os.environ[key] = value
        status["openai"] = bool(os.getenv("OPENAI_API_KEY", ""))
        status["tavily"] = bool(os.getenv("TAVILY_API_KEY", ""))
    except FileNotFoundError:
        # No secrets file — local dev relies on .env loaded above
        status["openai"] = bool(os.getenv("OPENAI_API_KEY", ""))
        status["tavily"] = bool(os.getenv("TAVILY_API_KEY", ""))
    except Exception as exc:
        logging.getLogger(__name__).warning("Secrets load warning: %s", exc)
    return status


_secrets_status = _load_streamlit_secrets()

# ── 3. Now safe to import services (they call os.getenv at instantiation) ─────
from services.claim_extractor import ClaimExtractor          # noqa: E402
from services.demo_data import load_demo_session             # noqa: E402
from services.pdf_parser import PDFParser                    # noqa: E402
from services.pipeline import FactCheckPipeline              # noqa: E402
from services.report_generator import ReportGenerator        # noqa: E402
from services.verifier import Verifier                       # noqa: E402
from ui.components import (                                  # noqa: E402
    render_architecture_panel,
    render_dashboard_header,
    render_hero,
    render_roadmap_panel,
    render_security_panel,
    render_solution_overview,
    render_summary_panel,
    render_verification_results,
    render_workflow,
)
from ui.theme import PPT_THEME_CSS                           # noqa: E402
from utils.constants import (                                # noqa: E402
    APP_NAME,
    ERROR_API_KEY,
    HUMAN_REVIEW_THRESHOLD,
    MAX_PDF_SIZE_MB,
    STATUS_COLORS,
    STATUS_UNVERIFIABLE,
    SUPPORTED_MODELS,
    get_default_model,
)
from utils.helpers import (                                  # noqa: E402
    calculate_claim_statistics,
    truncate_text,
    validate_pdf_file,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
SAMPLE_PDF_PATH = BASE_DIR / "assets" / "sample_report.pdf"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(PPT_THEME_CSS, unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def has_required_keys() -> bool:
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
    return bool(
        openai_key
        and tavily_key
        and not openai_key.startswith("sk-your")
        and not tavily_key.startswith("tvly-your")
        and len(openai_key) > 20
        and len(tavily_key) > 20
    )


def init_state() -> None:
    defaults = {
        "extracted_text": "",
        "extracted_claims": [],
        "verification_results": [],
        "document_name": "",
        "document_metadata": {},
        "workflow_step": 1,
        "demo_mode": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def set_workflow_step(step: int) -> None:
    st.session_state.workflow_step = max(1, min(step, 8))


# ── Sidebar ───────────────────────────────────────────────────────────────────
def sidebar_controls():
    with st.sidebar:
        # Sidebar branding
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-logo">🔍</div>
                <div>
                    <div class="sidebar-title">FactCheck AI</div>
                    <div class="sidebar-sub">PDF Claim Verifier</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # API status pill — no keys exposed, just green/red dot
        if has_required_keys():
            st.markdown('<div class="api-status ok">⬤ &nbsp;API Connected</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="api-status warn">⬤ &nbsp;API Keys Missing</div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section-label">DOCUMENT</div>', unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Upload PDF",
            type=["pdf"],
            help=f"Maximum size: {MAX_PDF_SIZE_MB} MB.",
            label_visibility="collapsed",
        )

        if SAMPLE_PDF_PATH.exists():
            with open(SAMPLE_PDF_PATH, "rb") as f:
                st.download_button(
                    "⬇️ Download Sample PDF",
                    data=f.read(),
                    file_name="sample_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

        st.markdown('<div class="sidebar-section-label">MODEL & SETTINGS</div>', unsafe_allow_html=True)
        _default = get_default_model()
        model = st.selectbox(
            "AI Model",
            SUPPORTED_MODELS,
            index=SUPPORTED_MODELS.index(_default) if _default in SUPPORTED_MODELS else 0,
            label_visibility="collapsed",
        )
        remove_duplicates = st.toggle("🔄 Remove duplicate claims", value=True)
        max_claims = st.slider("📊 Max claims", 5, 100, 40, step=5)
        min_confidence = st.slider(
            "🎯 Min confidence",
            0, 100, 0, step=5,
            help=f"Claims below {HUMAN_REVIEW_THRESHOLD}% are flagged for human review.",
        )

        st.markdown('<div class="sidebar-section-label">DEMO</div>', unsafe_allow_html=True)
        if st.button("🎬 Load Demo Dashboard", use_container_width=True):
            load_demo_session(st.session_state)
            st.rerun()

        if st.session_state.get("demo_mode"):
            st.markdown('<div class="demo-badge">⚡ Demo session active</div>', unsafe_allow_html=True)

    return uploaded_file, model, remove_duplicates, max_claims, min_confidence


# ── Pipeline actions ──────────────────────────────────────────────────────────
def reset_for_new_file(uploaded_file) -> None:
    if uploaded_file and uploaded_file.name != st.session_state.document_name:
        st.session_state.update({
            "extracted_text": "",
            "extracted_claims": [],
            "verification_results": [],
            "document_metadata": {},
            "document_name": uploaded_file.name,
            "demo_mode": False,
        })
        set_workflow_step(1)


def apply_pipeline_result(result: dict) -> None:
    st.session_state.update({
        "extracted_text": result["extracted_text"],
        "extracted_claims": result["extracted_claims"],
        "verification_results": result["verification_results"],
        "document_metadata": result["document_metadata"],
        "document_name": result["document_name"],
        "demo_mode": False,
    })
    set_workflow_step(8)


def extract_text_and_claims(
    uploaded_file, model: str, remove_duplicates: bool, max_claims: int
) -> None:
    if not has_required_keys():
        st.error(ERROR_API_KEY)
        return

    is_valid, error = validate_pdf_file(uploaded_file)
    if not is_valid:
        st.error(error)
        return

    parser = PDFParser()
    progress = st.progress(0, text="Step 2/8 · Reading PDF...")
    try:
        set_workflow_step(2)
        text, pdf_error = parser.extract_text(uploaded_file)
        if pdf_error:
            progress.empty()
            st.error(f"Failed to extract text from PDF: {pdf_error}")
            set_workflow_step(1)
            return

        st.session_state.extracted_text = text
        st.session_state.document_metadata = parser.get_pdf_metadata(uploaded_file)
        progress.progress(35, text="Step 3/8 · Extracting factual claims...")

        extractor = ClaimExtractor(model=model)
        claims, claim_error = extractor.extract_and_process_claims(
            text, remove_duplicates=remove_duplicates, max_claims=max_claims,
        )
        progress.progress(100, text="Steps 3–4 complete · Claims extracted.")
        progress.empty()

        if claim_error:
            st.error(f"Failed to extract claims: {claim_error}")
            set_workflow_step(2)
            return

        st.session_state.extracted_claims = claims
        st.session_state.verification_results = []
        st.session_state.demo_mode = False
        set_workflow_step(4)
        st.success(f"Extracted {len(claims)} factual claims.")
    except Exception as exc:
        logger.exception("Unexpected error during extraction: %s", exc)
        progress.empty()
        st.error(f"An unexpected error occurred: {exc}")


def verify_claims(model: str, min_confidence: int) -> None:
    if not has_required_keys():
        st.error(ERROR_API_KEY)
        return

    claims = st.session_state.extracted_claims
    if not claims:
        st.warning("Extract claims before starting verification.")
        return

    verifier = Verifier(model=model)
    progress = st.progress(0, text="Step 5/8 · Searching live web evidence...")
    status_placeholder = st.empty()

    def on_progress(current: int, total: int) -> None:
        pct = int((current / total) * 100) if total else 0
        label = f"Step 5/8 · Web search ({current}/{total})" if pct < 70 else f"Step 6/8 · AI verdict ({current}/{total})"
        progress.progress(pct, text=label)
        status_placeholder.caption(f"Checking claim {min(current + 1, total)} of {total}")

    try:
        set_workflow_step(5)
        results, error = verifier.verify_claims(
            claims, progress_callback=on_progress, min_confidence=min_confidence,
        )
        progress.progress(100, text="Steps 6–7 complete · Confidence scores assigned.")
        status_placeholder.empty()
        progress.empty()

        if error:
            st.error(f"Verification failed: {error}")
            return

        st.session_state.verification_results = results
        st.session_state.demo_mode = False
        set_workflow_step(7)
        review_count = sum(1 for r in results if r.get("needs_review"))
        st.success(f"Verified {len(results)} claims. {review_count} flagged for human review.")
    except Exception as exc:
        logger.exception("Unexpected error during verification: %s", exc)
        progress.empty()
        status_placeholder.empty()
        st.error(f"An unexpected error occurred: {exc}")


def run_full_pipeline(
    uploaded_file, model: str, remove_duplicates: bool,
    max_claims: int, min_confidence: int,
) -> None:
    if not has_required_keys():
        st.error(ERROR_API_KEY)
        return

    pipeline = FactCheckPipeline(model=model)
    progress = st.progress(0, text="Starting full verification pipeline...")
    status_placeholder = st.empty()

    def on_progress(message: str, percent: int) -> None:
        progress.progress(min(percent, 100), text=message)
        status_placeholder.caption(message)

    try:
        result, error = pipeline.run(
            uploaded_file,
            remove_duplicates=remove_duplicates,
            max_claims=max_claims,
            min_confidence=min_confidence,
            progress_callback=on_progress,
        )
        progress.empty()
        status_placeholder.empty()

        if error:
            st.error(error)
            return

        apply_pipeline_result(result)
        review_count = sum(1 for r in result["verification_results"] if r.get("needs_review"))
        st.success(
            f"Pipeline complete: {len(result['extracted_claims'])} claims extracted, "
            f"{len(result['verification_results'])} verified, {review_count} need review."
        )
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        progress.empty()
        status_placeholder.empty()
        st.error(f"Pipeline failed: {exc}")


# ── Render panels ─────────────────────────────────────────────────────────────
def render_upload_panel(
    uploaded_file, model: str, remove_duplicates: bool,
    max_claims: int, min_confidence: int,
) -> None:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">📄 Upload Document</div>
            <p class="section-desc">Drop PDF here or use the sidebar uploader to begin.</p>
            <div class="upload-dropzone">
                <strong>PDF only</strong><br>
                Text-based PDFs work best · Scanned PDFs may need OCR
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not uploaded_file:
        st.info("Upload a PDF from the sidebar, download the sample PDF, or click **Load Demo Dashboard**.")
        return

    set_workflow_step(max(st.session_state.workflow_step, 1))
    is_valid, error = validate_pdf_file(uploaded_file)
    if error:
        st.error(error)
    else:
        st.success(f"Selected: {uploaded_file.name} ({uploaded_file.size / 1048576:.2f} MB)")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Extract Claims", use_container_width=True, disabled=not is_valid):
            extract_text_and_claims(uploaded_file, model, remove_duplicates, max_claims)
    with col2:
        if st.button("⚡ Run Full Pipeline", type="primary", use_container_width=True, disabled=not is_valid):
            run_full_pipeline(uploaded_file, model, remove_duplicates, max_claims, min_confidence)

    metadata = st.session_state.document_metadata
    if metadata:
        c1, c2, c3 = st.columns(3)
        c1.metric("Pages", metadata.get("pages", 0))
        c2.metric("File Size", f"{metadata.get('file_size_mb', 0):.2f} MB")
        c3.metric("Characters", f"{len(st.session_state.extracted_text):,}")


def render_claims_panel(model: str, min_confidence: int) -> None:
    claims = st.session_state.extracted_claims
    if not claims:
        return

    st.markdown("### 💬 Extracted Claims")
    rows = [{"#": i, "Claim": c["claim"], "Type": c["type"], "Status": "Pending"} for i, c in enumerate(claims, 1)]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if st.session_state.verification_results:
        st.caption("Verification already complete. Re-run only if you changed settings.")
        return

    if st.button("✅ Begin Verification", type="primary", use_container_width=True):
        verify_claims(model, min_confidence)


def render_detailed_report() -> None:
    results = st.session_state.verification_results
    if not results:
        st.info("Verification results will appear here after you run verification.")
        return

    stats = calculate_claim_statistics(results)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total", stats["total"])
    c2.metric("Verified", stats["verified"])
    c3.metric("Inaccurate", stats["inaccurate"])
    c4.metric("False", stats["false"])
    c5.metric("Avg Confidence", f"{stats['avg_confidence']}%")

    st.markdown("---")
    for index, result in enumerate(results, start=1):
        status = result.get("status", STATUS_UNVERIFIABLE)
        color = STATUS_COLORS.get(status, STATUS_COLORS[STATUS_UNVERIFIABLE])
        review_note = ""
        if result.get("needs_review"):
            review_note = (
                f"<br><span class='review-flag'>Needs human review: "
                f"{escape(str(result.get('review_reason', 'Low confidence')))}</span>"
            )

        with st.expander(
            f"{index}. {status} ({result.get('confidence', 0)}%) | "
            f"{truncate_text(result.get('claim', ''), 80)}",
            expanded=index <= 2,
        ):
            st.markdown(
                f"""
                <div class='result-card {_status_css(status)}'>
                <b>Claim:</b> {escape(str(result.get('claim', '')))}<br>
                <b>Type:</b> {escape(str(result.get('type', '')))}<br>
                <b>Status:</b> <span style='color:{color}; font-weight:bold;'>{escape(str(status))}</span><br>
                <b>Confidence:</b> {result.get('confidence', 0)}%<br>
                <b>Explanation:</b> {escape(str(result.get('explanation', '')))}
                {review_note}
                </div>
                """,
                unsafe_allow_html=True,
            )
            if result.get("key_finding"):
                st.markdown(f"**Key Finding:** {result['key_finding']}")
            if result.get("sources"):
                st.markdown("**Sources:**")
                for source in result["sources"]:
                    url = source.get("url", "")
                    title = source.get("title", "Source")
                    st.markdown(f"- [{title}]({url})" if url else f"- {title}")
            if result.get("evidence_snippet"):
                with st.popover("View Evidence"):
                    st.text(result["evidence_snippet"])


def _status_css(status: str) -> str:
    return {"Verified": "verified", "Inaccurate": "inaccurate", "False": "false"}.get(status, "unverifiable")


def render_download_panel() -> None:
    results = st.session_state.verification_results
    if not results:
        st.info("Run verification to generate stakeholder-ready reports.")
        return

    generator = ReportGenerator()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    set_workflow_step(8)

    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Multi-Format Report Generation</div>
            <p class="section-desc">Every verification session exports a stakeholder-ready report.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='report-card'><h4>📊 CSV Export</h4><div class='report-audience'>Analysts & Data Teams</div></div>", unsafe_allow_html=True)
        csv_data, csv_err = generator.generate_csv_report(results)
        if csv_err:
            st.error(csv_err)
        else:
            st.download_button("Download CSV", data=csv_data, file_name=f"factcheck_report_{timestamp}.csv", mime="text/csv", use_container_width=True, key="csv_download")

    with col2:
        st.markdown("<div class='report-card'><h4>📄 PDF Report</h4><div class='report-audience'>Executives & Clients</div></div>", unsafe_allow_html=True)
        pdf_data, pdf_err = generator.generate_pdf_report(results)
        if pdf_err:
            st.error(pdf_err)
        else:
            st.download_button("Download PDF", data=pdf_data, file_name=f"factcheck_report_{timestamp}.pdf", mime="application/pdf", use_container_width=True, key="pdf_download")

    with col3:
        st.markdown("<div class='report-card'><h4>📝 Markdown Export</h4><div class='report-audience'>Developers & Docs Teams</div></div>", unsafe_allow_html=True)
        md_data, md_err = generator.generate_markdown_report(results)
        if md_err:
            st.error(md_err)
        else:
            st.download_button("Download Markdown", data=md_data, file_name=f"factcheck_report_{timestamp}.md", mime="text/markdown", use_container_width=True, key="md_download")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    init_state()
    render_hero()

    uploaded_file, model, remove_duplicates, max_claims, min_confidence = sidebar_controls()
    reset_for_new_file(uploaded_file)

    if not has_required_keys() and not st.session_state.get("demo_mode"):
        st.markdown(
            """
            <div class="banner-warn">
                🔑 <strong>API keys not configured.</strong>
                Add <code>OPENAI_API_KEY</code> and <code>TAVILY_API_KEY</code> to Streamlit Cloud secrets,
                or click <strong>Load Demo Dashboard</strong> to explore the UI.
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_dashboard_header()
    render_workflow(st.session_state.workflow_step)

    left, right = st.columns([1.05, 1], gap="large")
    with left:
        render_upload_panel(uploaded_file, model, remove_duplicates, max_claims, min_confidence)
        render_claims_panel(model, min_confidence)
    with right:
        render_summary_panel(st.session_state.verification_results)
        render_verification_results(st.session_state.verification_results)

    tab_report, tab_download, tab_about = st.tabs([
        "📊 Detailed Report", "📥 Download Reports", "ℹ️ About Project",
    ])
    with tab_report:
        render_detailed_report()
    with tab_download:
        render_download_panel()
    with tab_about:
        st.markdown("### Solution Overview")
        render_solution_overview()
        st.markdown("### Security & Reliability")
        render_security_panel()
        st.markdown("### System Architecture")
        render_architecture_panel()
        st.markdown("### Future Roadmap")
        render_roadmap_panel()


if __name__ == "__main__":
    main()
