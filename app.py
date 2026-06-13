"""FactCheck AI — Streamlit application."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

# ── MUST be the very first Streamlit call ─────────────────────────────────────
st.set_page_config(
    page_title="FactCheck AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load .env for local dev (silent no-op on Streamlit Cloud) ─────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ── Load Streamlit Cloud secrets → os.environ ─────────────────────────────────
# Must run AFTER set_page_config, before any service is imported.
_SECRET_KEYS = (
    "OPENAI_API_KEY",
    "TAVILY_API_KEY",
    "LLM_MODEL",
    "SEARCH_RESULTS_COUNT",
    "REQUEST_TIMEOUT_SECONDS",
)

def _load_secrets() -> None:
    """Write every Streamlit secret into os.environ."""
    try:
        _secrets = st.secrets
    except FileNotFoundError:
        return  # local dev with no secrets.toml — rely on .env
    except Exception as exc:
        logging.getLogger(__name__).warning("st.secrets unavailable: %s", exc)
        return

    for key in _SECRET_KEYS:
        # Don't overwrite a value already in the environment
        if os.environ.get(key, "").strip():
            continue
        value: str | None = None
        try:
            if key in _secrets:
                value = str(_secrets[key]).strip() or None
            elif "general" in _secrets and key in _secrets["general"]:
                value = str(_secrets["general"][key]).strip() or None
        except Exception:
            continue
        if value:
            os.environ[key] = value

_load_secrets()

# Debug — prints to Streamlit Cloud logs (visible in app logs tab)
print("=== FactCheck AI startup ===")
print("OPENAI_API_KEY set:", bool(os.environ.get("OPENAI_API_KEY")))
print("TAVILY_API_KEY set:", bool(os.environ.get("TAVILY_API_KEY")))

# ── Service imports (safe now that env vars are populated) ────────────────────
from services.claim_extractor import ClaimExtractor      # noqa: E402
from services.demo_data import load_demo_session         # noqa: E402
from services.pdf_parser import PDFParser                # noqa: E402
from services.pipeline import FactCheckPipeline          # noqa: E402
from services.report_generator import ReportGenerator    # noqa: E402
from services.verifier import Verifier                   # noqa: E402
from ui.components import (                              # noqa: E402
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
from ui.theme import PPT_THEME_CSS                       # noqa: E402
from utils.constants import (                            # noqa: E402
    APP_NAME,
    ERROR_API_KEY,
    HUMAN_REVIEW_THRESHOLD,
    MAX_PDF_SIZE_MB,
    STATUS_COLORS,
    STATUS_UNVERIFIABLE,
    SUPPORTED_MODELS,
    get_default_model,
)
from utils.helpers import (                              # noqa: E402
    calculate_claim_statistics,
    truncate_text,
    validate_pdf_file,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

st.markdown(PPT_THEME_CSS, unsafe_allow_html=True)

BASE_DIR = Path(__file__).parent
SAMPLE_PDF_PATH = BASE_DIR / "assets" / "sample_report.pdf"


# ── Key helpers ───────────────────────────────────────────────────────────────
def has_required_keys() -> bool:
    openai = os.environ.get("OPENAI_API_KEY", "").strip()
    tavily = os.environ.get("TAVILY_API_KEY", "").strip()
    return bool(openai and tavily)


def init_state() -> None:
    for key, val in {
        "extracted_text": "",
        "extracted_claims": [],
        "verification_results": [],
        "document_name": "",
        "document_metadata": {},
        "workflow_step": 1,
        "demo_mode": False,
        "show_debug": False,
    }.items():
        st.session_state.setdefault(key, val)


def set_workflow_step(step: int) -> None:
    st.session_state.workflow_step = max(1, min(step, 8))


# ── Sidebar ───────────────────────────────────────────────────────────────────
def sidebar_controls():
    with st.sidebar:
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

        # API status pill
        if has_required_keys():
            st.markdown(
                '<div class="api-status ok">⬤ &nbsp;API Connected</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="api-status warn">⬤ &nbsp;API Keys Missing</div>',
                unsafe_allow_html=True,
            )

        # ── Debug panel (toggle) ──────────────────────────────────────────────
        with st.expander("🛠 Debug / Key Status", expanded=not has_required_keys()):
            openai_val = os.environ.get("OPENAI_API_KEY", "")
            tavily_val = os.environ.get("TAVILY_API_KEY", "")
            openai_set = bool(openai_val.strip())
            tavily_set = bool(tavily_val.strip())

            # Show masked key preview so you can confirm the right key loaded
            def _preview(v: str) -> str:
                v = v.strip()
                if not v:
                    return "❌ not set"
                if len(v) < 8:
                    return "❌ too short"
                return f"✅ {v[:6]}...{v[-4:]}"

            st.markdown(
                f"**OpenAI key:** {_preview(openai_val)}  \n"
                f"**Tavily key:** {_preview(tavily_val)}  \n"
                f"**Keys valid:** {'✅ Yes — ready to verify' if has_required_keys() else '❌ No'}"
            )
            st.caption(
                "If both show ❌, your Streamlit Cloud secrets are not saved correctly. "
                "Go to App Settings → Secrets and verify the keys are present and non-empty."
            )
            new_openai = st.text_input(
                "OpenAI API Key",
                type="password",
                placeholder="sk-proj-...",
                key="dbg_openai",
            )
            new_tavily = st.text_input(
                "Tavily API Key",
                type="password",
                placeholder="tvly-...",
                key="dbg_tavily",
            )
            if st.button("Apply Keys", use_container_width=True):
                if new_openai.strip():
                    os.environ["OPENAI_API_KEY"] = new_openai.strip()
                if new_tavily.strip():
                    os.environ["TAVILY_API_KEY"] = new_tavily.strip()
                st.rerun()

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
            "🎯 Min confidence", 0, 100, 0, step=5,
            help=f"Claims below {HUMAN_REVIEW_THRESHOLD}% are flagged for review.",
        )

        st.markdown('<div class="sidebar-section-label">DEMO</div>', unsafe_allow_html=True)
        if st.button("🎬 Load Demo Dashboard", use_container_width=True):
            load_demo_session(st.session_state)
            st.rerun()

        if st.session_state.get("demo_mode"):
            st.markdown('<div class="demo-badge">⚡ Demo session active</div>', unsafe_allow_html=True)

    return uploaded_file, model, remove_duplicates, max_claims, min_confidence


# ── Pipeline helpers ──────────────────────────────────────────────────────────
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
    is_valid, err = validate_pdf_file(uploaded_file)
    if not is_valid:
        st.error(err)
        return

    parser = PDFParser()
    prog = st.progress(0, text="Step 2/8 · Reading PDF...")
    try:
        set_workflow_step(2)
        text, pdf_err = parser.extract_text(uploaded_file)
        if pdf_err:
            prog.empty()
            st.error(f"PDF read error: {pdf_err}")
            set_workflow_step(1)
            return

        st.session_state.extracted_text = text
        st.session_state.document_metadata = parser.get_pdf_metadata(uploaded_file)
        prog.progress(35, text="Step 3/8 · Extracting claims...")

        extractor = ClaimExtractor(model=model)
        claims, claim_err = extractor.extract_and_process_claims(
            text, remove_duplicates=remove_duplicates, max_claims=max_claims,
        )
        prog.progress(100, text="Done.")
        prog.empty()

        if claim_err:
            st.error(f"Claim extraction failed: {claim_err}")
            set_workflow_step(2)
            return

        st.session_state.extracted_claims = claims
        st.session_state.verification_results = []
        st.session_state.demo_mode = False
        set_workflow_step(4)
        st.success(f"Extracted {len(claims)} factual claims.")
    except Exception as exc:
        logger.exception("Extraction error: %s", exc)
        prog.empty()
        st.error(f"Unexpected error: {exc}")


def verify_claims(model: str, min_confidence: int) -> None:
    if not has_required_keys():
        st.error(ERROR_API_KEY)
        return
    claims = st.session_state.extracted_claims
    if not claims:
        st.warning("Extract claims first.")
        return

    verifier = Verifier(model=model)
    prog = st.progress(0, text="Step 5/8 · Searching web evidence...")
    slot = st.empty()

    def on_progress(current: int, total: int) -> None:
        pct = int((current / total) * 100) if total else 0
        label = (f"Step 5/8 · Search ({current}/{total})" if pct < 70
                 else f"Step 6/8 · AI verdict ({current}/{total})")
        prog.progress(pct, text=label)
        slot.caption(f"Claim {min(current + 1, total)} of {total}")

    try:
        set_workflow_step(5)
        results, err = verifier.verify_claims(
            claims, progress_callback=on_progress, min_confidence=min_confidence,
        )
        prog.progress(100, text="Done.")
        slot.empty()
        prog.empty()
        if err:
            st.error(f"Verification failed: {err}")
            return
        st.session_state.verification_results = results
        st.session_state.demo_mode = False
        set_workflow_step(7)
        review_count = sum(1 for r in results if r.get("needs_review"))
        st.success(f"Verified {len(results)} claims. {review_count} flagged for review.")
    except Exception as exc:
        logger.exception("Verification error: %s", exc)
        prog.empty()
        slot.empty()
        st.error(f"Unexpected error: {exc}")


def run_full_pipeline(
    uploaded_file, model: str, remove_duplicates: bool,
    max_claims: int, min_confidence: int,
) -> None:
    if not has_required_keys():
        st.error(ERROR_API_KEY)
        return

    pipeline = FactCheckPipeline(model=model)
    prog = st.progress(0, text="Starting pipeline...")
    slot = st.empty()

    def on_progress(msg: str, pct: int) -> None:
        prog.progress(min(pct, 100), text=msg)
        slot.caption(msg)

    try:
        result, err = pipeline.run(
            uploaded_file,
            remove_duplicates=remove_duplicates,
            max_claims=max_claims,
            min_confidence=min_confidence,
            progress_callback=on_progress,
        )
        prog.empty()
        slot.empty()
        if err:
            st.error(err)
            return
        apply_pipeline_result(result)
        review_count = sum(1 for r in result["verification_results"] if r.get("needs_review"))
        st.success(
            f"Done: {len(result['extracted_claims'])} claims, "
            f"{len(result['verification_results'])} verified, {review_count} for review."
        )
    except Exception as exc:
        logger.exception("Pipeline error: %s", exc)
        prog.empty()
        slot.empty()
        st.error(f"Pipeline failed: {exc}")


# ── Render helpers ────────────────────────────────────────────────────────────
def render_upload_panel(
    uploaded_file, model: str, remove_duplicates: bool,
    max_claims: int, min_confidence: int,
) -> None:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">📄 Upload Document</div>
            <p class="section-desc">Use the sidebar uploader to begin, or load the demo session.</p>
            <div class="upload-dropzone">
                <strong>PDF only</strong><br>
                Text-based PDFs work best · Scanned PDFs may need OCR
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not uploaded_file:
        st.info("Upload a PDF from the sidebar or click **Load Demo Dashboard**.")
        return

    set_workflow_step(max(st.session_state.workflow_step, 1))
    is_valid, err = validate_pdf_file(uploaded_file)
    if err:
        st.error(err)
    else:
        st.success(f"Selected: {uploaded_file.name} ({uploaded_file.size / 1048576:.2f} MB)")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 Extract Claims", use_container_width=True, disabled=not is_valid):
            extract_text_and_claims(uploaded_file, model, remove_duplicates, max_claims)
    with c2:
        if st.button("⚡ Run Full Pipeline", type="primary", use_container_width=True, disabled=not is_valid):
            run_full_pipeline(uploaded_file, model, remove_duplicates, max_claims, min_confidence)

    meta = st.session_state.document_metadata
    if meta:
        c1, c2, c3 = st.columns(3)
        c1.metric("Pages", meta.get("pages", 0))
        c2.metric("File Size", f"{meta.get('file_size_mb', 0):.2f} MB")
        c3.metric("Characters", f"{len(st.session_state.extracted_text):,}")


def render_claims_panel(model: str, min_confidence: int) -> None:
    claims = st.session_state.extracted_claims
    if not claims:
        return
    st.markdown("### 💬 Extracted Claims")
    rows = [{"#": i, "Claim": c["claim"], "Type": c["type"], "Status": "Pending"}
            for i, c in enumerate(claims, 1)]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    if st.session_state.verification_results:
        st.caption("Verification already complete.")
        return
    if st.button("✅ Begin Verification", type="primary", use_container_width=True):
        verify_claims(model, min_confidence)


def _status_css(status: str) -> str:
    return {"Verified": "verified", "Inaccurate": "inaccurate", "False": "false"}.get(
        status, "unverifiable"
    )


def render_detailed_report() -> None:
    results = st.session_state.verification_results
    if not results:
        st.info("Verification results appear here after you run verification.")
        return

    stats = calculate_claim_statistics(results)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total", stats["total"])
    c2.metric("Verified", stats["verified"])
    c3.metric("Inaccurate", stats["inaccurate"])
    c4.metric("False", stats["false"])
    c5.metric("Avg Confidence", f"{stats['avg_confidence']}%")
    st.markdown("---")

    for idx, result in enumerate(results, 1):
        status = result.get("status", STATUS_UNVERIFIABLE)
        color = STATUS_COLORS.get(status, STATUS_COLORS[STATUS_UNVERIFIABLE])
        review_note = ""
        if result.get("needs_review"):
            review_note = (
                f"<br><span class='review-flag'>Needs review: "
                f"{escape(str(result.get('review_reason', 'Low confidence')))}</span>"
            )
        with st.expander(
            f"{idx}. {status} ({result.get('confidence', 0)}%) | "
            f"{truncate_text(result.get('claim', ''), 80)}",
            expanded=idx <= 2,
        ):
            st.markdown(
                f"""
                <div class='result-card {_status_css(status)}'>
                <b>Claim:</b> {escape(str(result.get('claim', '')))}<br>
                <b>Type:</b> {escape(str(result.get('type', '')))}<br>
                <b>Status:</b> <span style='color:{color};font-weight:bold'>{escape(str(status))}</span><br>
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
                for s in result["sources"]:
                    url, title = s.get("url", ""), s.get("title", "Source")
                    st.markdown(f"- [{title}]({url})" if url else f"- {title}")
            if result.get("evidence_snippet"):
                with st.popover("View Evidence"):
                    st.text(result["evidence_snippet"])


def render_download_panel() -> None:
    results = st.session_state.verification_results
    if not results:
        st.info("Run verification to generate reports.")
        return

    gen = ReportGenerator()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    set_workflow_step(8)

    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Multi-Format Report Generation</div>
            <p class="section-desc">Download your verification session as CSV, PDF, or Markdown.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='report-card'><h4>📊 CSV</h4><div class='report-audience'>Analysts & Data Teams</div></div>", unsafe_allow_html=True)
        data, err = gen.generate_csv_report(results)
        if err:
            st.error(err)
        else:
            st.download_button("Download CSV", data=data, file_name=f"factcheck_{ts}.csv", mime="text/csv", use_container_width=True, key="csv_dl")

    with c2:
        st.markdown("<div class='report-card'><h4>📄 PDF</h4><div class='report-audience'>Executives & Clients</div></div>", unsafe_allow_html=True)
        data, err = gen.generate_pdf_report(results)
        if err:
            st.error(err)
        else:
            st.download_button("Download PDF", data=data, file_name=f"factcheck_{ts}.pdf", mime="application/pdf", use_container_width=True, key="pdf_dl")

    with c3:
        st.markdown("<div class='report-card'><h4>📝 Markdown</h4><div class='report-audience'>Developers & Docs</div></div>", unsafe_allow_html=True)
        data, err = gen.generate_markdown_report(results)
        if err:
            st.error(err)
        else:
            st.download_button("Download MD", data=data, file_name=f"factcheck_{ts}.md", mime="text/markdown", use_container_width=True, key="md_dl")


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
                Add <code>OPENAI_API_KEY</code> and <code>TAVILY_API_KEY</code>
                in <strong>Streamlit Cloud → App Settings → Secrets</strong>,
                or use the <strong>🛠 Debug / Key Status</strong> panel in the sidebar
                to enter keys manually for this session.
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

    t1, t2, t3 = st.tabs(["📊 Detailed Report", "📥 Download Reports", "ℹ️ About"])
    with t1:
        render_detailed_report()
    with t2:
        render_download_panel()
    with t3:
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
