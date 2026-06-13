"""FactCheck AI Streamlit application — PPT-aligned working dashboard."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from services.claim_extractor import ClaimExtractor
from services.demo_data import load_demo_session
from services.pdf_parser import PDFParser
from services.pipeline import FactCheckPipeline
from services.report_generator import ReportGenerator
from services.verifier import Verifier
from ui.components import (
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
from ui.theme import PPT_THEME_CSS
from utils.constants import (
    APP_NAME,
    ERROR_API_KEY,
    HUMAN_REVIEW_THRESHOLD,
    MAX_PDF_SIZE_MB,
    STATUS_COLORS,
    STATUS_UNVERIFIABLE,
    SUPPORTED_MODELS,
    get_default_model,
)
from utils.helpers import calculate_claim_statistics, truncate_text, validate_pdf_file


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()
BASE_DIR = Path(__file__).parent
SAMPLE_PDF_PATH = BASE_DIR / "assets" / "sample_report.pdf"


def configure_cloud_secrets() -> None:
    """Pull all secrets from Streamlit secrets into os.environ before any service runs."""
    all_keys = (
        "OPENAI_API_KEY",
        "TAVILY_API_KEY",
        "LLM_MODEL",
        "SEARCH_RESULTS_COUNT",
        "REQUEST_TIMEOUT_SECONDS",
    )
    try:
        for key in all_keys:
            if not os.getenv(key) and key in st.secrets:
                os.environ[key] = str(st.secrets[key])
    except Exception:
        pass


configure_cloud_secrets()

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(PPT_THEME_CSS, unsafe_allow_html=True)


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


def has_required_keys() -> bool:
    openai_key = os.getenv("OPENAI_API_KEY", "")
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    return bool(
        openai_key
        and tavily_key
        and not openai_key.startswith("sk-your")
        and not tavily_key.startswith("tvly-your")
        and len(openai_key) > 20
        and len(tavily_key) > 20
    )


def set_workflow_step(step: int) -> None:
    st.session_state.workflow_step = max(1, min(step, 8))


def apply_api_keys_from_sidebar() -> None:
    with st.sidebar.expander("🔑 API Keys", expanded=not has_required_keys()):
        openai_key = st.text_input(
            "OpenAI API Key",
            value=os.getenv("OPENAI_API_KEY", ""),
            type="password",
            placeholder="sk-...",
        )
        tavily_key = st.text_input(
            "Tavily API Key",
            value=os.getenv("TAVILY_API_KEY", ""),
            type="password",
            placeholder="tvly-...",
        )
        if openai_key.strip():
            os.environ["OPENAI_API_KEY"] = openai_key.strip()
        if tavily_key.strip():
            os.environ["TAVILY_API_KEY"] = tavily_key.strip()

        if has_required_keys():
            st.success("API keys configured for this session.")
        else:
            st.warning("Add both keys to run live PDF verification.")


def sidebar_controls():
    apply_api_keys_from_sidebar()

    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        st.caption("Upload a PDF, run the pipeline, or load the demo session.")
        st.divider()

        uploaded_file = st.file_uploader(
            "📄 Upload Document",
            type=["pdf"],
            help=f"Maximum size: {MAX_PDF_SIZE_MB} MB.",
        )

        if SAMPLE_PDF_PATH.exists():
            with open(SAMPLE_PDF_PATH, "rb") as sample_file:
                st.download_button(
                    "⬇️ Download Sample PDF",
                    data=sample_file.read(),
                    file_name="sample_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

        st.divider()
        _default_model = get_default_model()
        model = st.selectbox(
            "🤖 AI Model",
            SUPPORTED_MODELS,
            index=SUPPORTED_MODELS.index(_default_model) if _default_model in SUPPORTED_MODELS else 0,
        )
        remove_duplicates = st.toggle("🔄 Remove duplicate claims", value=True)
        max_claims = st.slider("📊 Maximum claims", 5, 100, 40, step=5)
        min_confidence = st.slider(
            "🎯 Minimum confidence to show",
            0,
            100,
            0,
            step=5,
            help=f"Claims below {HUMAN_REVIEW_THRESHOLD}% are flagged for human review.",
        )

        st.divider()
        if st.button("🎬 Load Demo Dashboard", use_container_width=True):
            load_demo_session(st.session_state)
            st.rerun()

        if st.session_state.get("demo_mode"):
            st.info("Demo session loaded. Upload a PDF and run live verification anytime.")

    return uploaded_file, model, remove_duplicates, max_claims, min_confidence


def reset_for_new_file(uploaded_file) -> None:
    if uploaded_file and uploaded_file.name != st.session_state.document_name:
        st.session_state.extracted_text = ""
        st.session_state.extracted_claims = []
        st.session_state.verification_results = []
        st.session_state.document_metadata = {}
        st.session_state.document_name = uploaded_file.name
        st.session_state.demo_mode = False
        set_workflow_step(1)


def apply_pipeline_result(result: dict) -> None:
    st.session_state.extracted_text = result["extracted_text"]
    st.session_state.extracted_claims = result["extracted_claims"]
    st.session_state.verification_results = result["verification_results"]
    st.session_state.document_metadata = result["document_metadata"]
    st.session_state.document_name = result["document_name"]
    st.session_state.demo_mode = False
    set_workflow_step(8)


def extract_text_and_claims(uploaded_file, model: str, remove_duplicates: bool, max_claims: int) -> None:
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
            text,
            remove_duplicates=remove_duplicates,
            max_claims=max_claims,
        )
        progress.progress(100, text="Steps 3–4 complete · Claims extracted and deduplicated.")
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
    status = st.empty()

    def on_progress(current: int, total: int) -> None:
        percent = int((current / total) * 100) if total else 0
        if percent < 70:
            progress.progress(percent, text=f"Step 5/8 · Web search ({current}/{total})")
        else:
            progress.progress(percent, text=f"Step 6/8 · AI verdict ({current}/{total})")
        status.caption(f"Checking claim {min(current + 1, total)} of {total}")

    try:
        set_workflow_step(5)
        results, error = verifier.verify_claims(
            claims,
            progress_callback=on_progress,
            min_confidence=min_confidence,
        )
        progress.progress(100, text="Steps 6–7 complete · Confidence scores assigned.")
        status.empty()
        progress.empty()

        if error:
            st.error(f"Verification failed: {error}")
            return

        st.session_state.verification_results = results
        st.session_state.demo_mode = False
        set_workflow_step(7)
        review_count = sum(1 for item in results if item.get("needs_review"))
        st.success(f"Verified {len(results)} claims. {review_count} flagged for human review.")
    except Exception as exc:
        logger.exception("Unexpected error during verification: %s", exc)
        progress.empty()
        status.empty()
        st.error(f"An unexpected error occurred: {exc}")


def run_full_pipeline(
    uploaded_file,
    model: str,
    remove_duplicates: bool,
    max_claims: int,
    min_confidence: int,
) -> None:
    if not has_required_keys():
        st.error(ERROR_API_KEY)
        return

    pipeline = FactCheckPipeline(model=model)
    progress = st.progress(0, text="Starting full verification pipeline...")
    status = st.empty()

    def on_progress(message: str, percent: int) -> None:
        progress.progress(min(percent, 100), text=message)
        status.caption(message)

    try:
        result, error = pipeline.run(
            uploaded_file,
            remove_duplicates=remove_duplicates,
            max_claims=max_claims,
            min_confidence=min_confidence,
            progress_callback=on_progress,
        )
        progress.empty()
        status.empty()

        if error:
            st.error(error)
            return

        apply_pipeline_result(result)
        review_count = sum(1 for item in result["verification_results"] if item.get("needs_review"))
        st.success(
            f"Pipeline complete: {len(result['extracted_claims'])} claims extracted, "
            f"{len(result['verification_results'])} verified, {review_count} need review."
        )
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        progress.empty()
        status.empty()
        st.error(f"Pipeline failed: {exc}")


def render_upload_panel(uploaded_file, model: str, remove_duplicates: bool, max_claims: int, min_confidence: int) -> None:
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
        size_mb = uploaded_file.size / (1024 * 1024)
        st.success(f"Selected: {uploaded_file.name} ({size_mb:.2f} MB)")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Extract Claims", use_container_width=True, disabled=not is_valid):
            extract_text_and_claims(uploaded_file, model, remove_duplicates, max_claims)
    with col2:
        if st.button("⚡ Run Full Pipeline", type="primary", use_container_width=True, disabled=not is_valid):
            run_full_pipeline(uploaded_file, model, remove_duplicates, max_claims, min_confidence)

    metadata = st.session_state.document_metadata
    if metadata:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Pages", metadata.get("pages", 0))
        with col2:
            st.metric("File Size", f"{metadata.get('file_size_mb', 0):.2f} MB")
        with col3:
            st.metric("Characters", f"{len(st.session_state.extracted_text):,}")


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
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total", stats["total"])
    col2.metric("Verified", stats["verified"])
    col3.metric("Inaccurate", stats["inaccurate"])
    col4.metric("False", stats["false"])
    col5.metric("Avg Confidence", f"{stats['avg_confidence']}%")

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
                    if url:
                        st.markdown(f"- [{title}]({url})")
                    else:
                        st.markdown(f"- {title}")

            if result.get("evidence_snippet"):
                with st.popover("View Evidence"):
                    st.text(result["evidence_snippet"])


def _status_css(status: str) -> str:
    return {
        "Verified": "verified",
        "Inaccurate": "inaccurate",
        "False": "false",
    }.get(status, "unverifiable")


def render_download_panel() -> None:
    results = st.session_state.verification_results
    if not results:
        st.info("Run verification to generate stakeholder-ready reports.")
        return

    generator = ReportGenerator()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    set_workflow_step(8)
    csv_error = pdf_error = md_error = None

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
        st.markdown(
            """
            <div class="report-card">
                <h4>📊 CSV Export</h4>
                <ul>
                    <li>One row per claim</li>
                    <li>Verdict + confidence + correction</li>
                    <li>Source URLs for each claim</li>
                </ul>
                <div class="report-audience">Ideal for: Analysts & Data Teams</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        csv_data, csv_error = generator.generate_csv_report(results)
        if csv_error:
            st.error(csv_error)
        else:
            st.download_button(
                "Download CSV",
                data=csv_data,
                file_name=f"factcheck_report_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True,
                key="csv_download",
            )

    with col2:
        st.markdown(
            """
            <div class="report-card">
                <h4>📄 PDF Report</h4>
                <ul>
                    <li>Executive summary section</li>
                    <li>Colour-coded claim table</li>
                    <li>Evidence excerpts included</li>
                </ul>
                <div class="report-audience">Ideal for: Executives & Clients</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        pdf_data, pdf_error = generator.generate_pdf_report(results)
        if pdf_error:
            st.error(pdf_error)
        else:
            st.download_button(
                "Download PDF",
                data=pdf_data,
                file_name=f"factcheck_report_{timestamp}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="pdf_download",
            )

    with col3:
        st.markdown(
            """
            <div class="report-card">
                <h4>📝 Markdown Export</h4>
                <ul>
                    <li>GitHub-compatible format</li>
                    <li>Clean heading structure</li>
                    <li>Hyperlinked source citations</li>
                </ul>
                <div class="report-audience">Ideal for: Developers & Docs Teams</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        md_data, md_error = generator.generate_markdown_report(results)
        if md_error:
            st.error(md_error)
        else:
            st.download_button(
                "Download Markdown",
                data=md_data,
                file_name=f"factcheck_report_{timestamp}.md",
                mime="text/markdown",
                use_container_width=True,
                key="md_download",
            )

    if not any([csv_error, pdf_error, md_error]):
        st.success("All report formats are ready to download.")


def main() -> None:
    init_state()
    render_hero()

    uploaded_file, model, remove_duplicates, max_claims, min_confidence = sidebar_controls()
    reset_for_new_file(uploaded_file)

    if not has_required_keys() and not st.session_state.get("demo_mode"):
        st.warning(
            "Live verification needs OpenAI and Tavily API keys. "
            "Enter them in the sidebar, or click **Load Demo Dashboard** to explore the working UI."
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
        "📊 Detailed Report",
        "📥 Download Reports",
        "ℹ️ About Project",
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
