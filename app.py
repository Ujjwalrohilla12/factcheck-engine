"""FactCheck AI Streamlit application."""

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
from services.pdf_parser import PDFParser
from services.report_generator import ReportGenerator
from services.verifier import Verifier
from utils.constants import (
    APP_NAME,
    DEFAULT_MODEL,
    ERROR_API_KEY,
    STATUS_COLORS,
    STATUS_UNVERIFIABLE,
    SUPPORTED_MODELS,
)
from utils.helpers import calculate_claim_statistics, truncate_text, validate_pdf_file

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()
BASE_DIR = Path(__file__).parent


def configure_cloud_secrets() -> None:
    """Expose Streamlit Cloud secrets through os.environ for service classes."""
    for key in ("OPENAI_API_KEY", "TAVILY_API_KEY"):
        try:
            if not os.getenv(key) and key in st.secrets:
                os.environ[key] = st.secrets[key]
        except Exception:
            continue


configure_cloud_secrets()

st.set_page_config(
    page_title=APP_NAME,
    page_icon=str(BASE_DIR / "assets" / "logo.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --primary: #60a5fa;
        --primary-dark: #3b82f6;
        --primary-light: #dbeafe;
        --success: #34d399;
        --warning: #fbbf24;
        --danger: #f87171;
        --dark: #1e293b;
        --light: #ffffff;
        --bg-light: #f8fafc;
        --border: #e2e8f0;
        --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.03);
        --shadow: 0 4px 6px rgba(0, 0, 0, 0.05), 0 10px 13px rgba(0, 0, 0, 0.03);
        --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.08);
        --shadow-xl: 0 20px 50px rgba(0, 0, 0, 0.1);
        --radius: 12px;
    }
    
    * {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    html, body {
        background: #ffffff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .block-container {
        padding-top: 2.5rem !important;
        max-width: 1400px !important;
        background: #ffffff !important;
    }
    
    /* Header Styling */
    .app-title {
        font-size: 3.5rem;
        font-weight: 900;
        margin: 0;
        color: #60a5fa;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 4px rgba(96, 165, 250, 0.1);
    }
    
    .muted {
        color: #64748b;
        margin-top: 0.75rem;
        font-size: 1.1rem;
        font-weight: 500;
        letter-spacing: 0.3px;
    }
    
    /* Cards & Containers */
    .status-card {
        border: none;
        border-left: 5px solid var(--primary);
        border-radius: var(--radius);
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        background: #f0f9ff;
        box-shadow: var(--shadow);
        border: 1px solid #bfdbfe;
    }
    
    .status-card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-4px);
        background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
    }
    
    .status-card.verified {
        border-left-color: var(--success);
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
    }
    
    .status-card.inaccurate {
        border-left-color: var(--warning);
        background: #fffbeb;
        border: 1px solid #fcd34d;
    }
    
    .status-card.false {
        border-left-color: var(--danger);
        background: #fef2f2;
        border: 1px solid #fca5a5;
    }
    
    .status-card.unverifiable {
        border-left-color: #94a3b8;
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
    }
    
    /* Metrics */
    div[data-testid="stMetric"] {
        background: #ffffff;
        padding: 1.75rem;
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        border: 1px solid #e2e8f0;
        position: relative;
        overflow: hidden;
    }
    
    div[data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary), var(--primary-light));
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 800;
        color: var(--primary);
        letter-spacing: -0.02em;
    }
    
    /* Buttons */
    button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        padding: 0.9rem 2.5rem !important;
        box-shadow: 0 4px 15px rgba(96, 165, 250, 0.2) !important;
        color: white !important;
        position: relative;
        overflow: hidden;
    }
    
    button[kind="primary"]::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        background: rgba(255,255,255,0.3);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    button[kind="primary"]:hover::before {
        width: 300px;
        height: 300px;
    }
    
    button[kind="primary"]:hover {
        box-shadow: 0 10px 30px rgba(96, 165, 250, 0.3) !important;
        transform: translateY(-2px);
    }
    
    button[kind="primary"]:active {
        transform: translateY(0);
    }
    
    /* Tabs */
    .stTabs {
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        border: none;
        background: #ffffff;
        border-radius: var(--radius);
        padding: 0.75rem;
        box-shadow: var(--shadow);
        border: 1px solid #e2e8f0;
        gap: 0.5rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important;
        color: white !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 15px rgba(96, 165, 250, 0.2);
    }
    
    .stTabs [aria-selected="false"] {
        color: #64748b !important;
    }
    
    /* Expanders */
    .stExpander {
        border-radius: var(--radius) !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: var(--shadow-sm) !important;
        background: #ffffff !important;
    }
    
    .stExpander:hover {
        box-shadow: var(--shadow) !important;
        border: 1px solid #bfdbfe !important;
        background: #f0f9ff !important;
    }
    
    /* Info/Success/Error boxes */
    .info-box {
        background: #dbeafe;
        border-left: 5px solid var(--primary);
        padding: 1.5rem;
        border-radius: var(--radius);
        color: #0c4a6e;
        font-weight: 600;
        box-shadow: var(--shadow-sm);
    }
    
    .success-box {
        background: #dcfce7;
        border-left: 5px solid var(--success);
        padding: 1.5rem;
        border-radius: var(--radius);
        color: #065f46;
        font-weight: 600;
        box-shadow: var(--shadow-sm);
    }
    
    .error-box {
        background: #fee2e2;
        border-left: 5px solid var(--danger);
        padding: 1.5rem;
        border-radius: var(--radius);
        color: #7f1d1d;
        font-weight: 600;
        box-shadow: var(--shadow-sm);
    }
    
    /* Text & Typography */
    h1, h2, h3, h4, h5, h6 {
        color: var(--dark);
        font-weight: 800;
        letter-spacing: -0.01em;
    }
    
    h1 { font-size: 2.5rem; margin: 2rem 0 1rem; }
    h2 { font-size: 2rem; margin: 1.75rem 0 0.75rem; }
    h3 { font-size: 1.5rem; margin: 1.5rem 0 0.75rem; }
    
    p {
        color: #64748b;
        line-height: 1.6;
        letter-spacing: 0.3px;
    }
    
    /* Data Table */
    .dataframe {
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow) !important;
        border: 1px solid #e2e8f0 !important;
        overflow: hidden;
        background: #ffffff !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
        margin: 2rem 0;
    }
    
    /* Popover */
    .stPopover {
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow-xl) !important;
        background: #ffffff !important;
    }
    
    /* Download container */
    .download-section {
        background: #ffffff;
        border-radius: var(--radius);
        padding: 2rem;
        box-shadow: var(--shadow);
        border: 1px solid #e2e8f0;
        margin-top: 2rem;
    }
    
    /* Animations */
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.7;
        }
    }
    
    .stContainer {
        animation: slideIn 0.5s ease-out;
    }
    
    /* Scroll bar styling */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #60a5fa, #3b82f6);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #3b82f6, #2563eb);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state() -> None:
    defaults = {
        "extracted_text": "",
        "extracted_claims": [],
        "verification_results": [],
        "document_name": "",
        "document_metadata": {},
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def has_required_keys() -> bool:
    return bool(os.getenv("OPENAI_API_KEY") and os.getenv("TAVILY_API_KEY"))


def sidebar_controls():
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        st.divider()
        
        st.markdown("#### 📤 **PDF Upload**")
        uploaded_file = st.file_uploader(
            "Choose a PDF document",
            type=["pdf"],
            help="Maximum size: 25 MB. Supports text-based PDFs.",
        )

        st.divider()
        st.markdown("#### 🔧 **Verification Settings**")
        
        model = st.selectbox(
            "🤖 AI Model",
            SUPPORTED_MODELS,
            index=SUPPORTED_MODELS.index(DEFAULT_MODEL) if DEFAULT_MODEL in SUPPORTED_MODELS else 0,
            help="gpt-4o-mini: Fast & affordable\ngpt-4o: Better quality"
        )
        
        remove_duplicates = st.toggle(
            "🔄 Remove duplicate claims",
            value=True,
            help="Removes similar claims to reduce redundancy"
        )
        
        max_claims = st.slider(
            "📊 Maximum claims to extract",
            5, 100, 40, step=5,
            help="Limits total claims extracted from the document"
        )
        
        min_confidence = st.slider(
            "🎯 Minimum confidence to show",
            0, 100, 0, step=5,
            help="Only display verified claims above this confidence level"
        )

        st.divider()
        st.caption("🔐 Uses Tavily live web search & OpenAI reasoning. Store API keys in `.env` locally or in Streamlit secrets for production.")

    return uploaded_file, model, remove_duplicates, max_claims, min_confidence


def reset_for_new_file(uploaded_file) -> None:
    if uploaded_file and uploaded_file.name != st.session_state.document_name:
        st.session_state.extracted_text = ""
        st.session_state.extracted_claims = []
        st.session_state.verification_results = []
        st.session_state.document_metadata = {}
        st.session_state.document_name = uploaded_file.name


def extract_text_and_claims(uploaded_file, model: str, remove_duplicates: bool, max_claims: int) -> None:
    logger.info(f"Starting claim extraction for file: {uploaded_file.name}")
    is_valid, error = validate_pdf_file(uploaded_file)
    if not is_valid:
        logger.error(f"PDF validation failed: {error}")
        st.error(error)
        return

    parser = PDFParser()
    progress = st.progress(0, text="Reading PDF...")
    try:
        text, pdf_error = parser.extract_text(uploaded_file)
        if pdf_error:
            logger.error(f"PDF parsing error: {pdf_error}")
            progress.empty()
            st.error(f"Failed to extract text from PDF: {pdf_error}")
            return

        st.session_state.extracted_text = text
        st.session_state.document_metadata = parser.get_pdf_metadata(uploaded_file)
        logger.info(f"Successfully extracted {len(text)} characters from PDF")
        progress.progress(35, text="Extracting factual claims...")

        extractor = ClaimExtractor(model=model)
        claims, claim_error = extractor.extract_and_process_claims(
            text,
            remove_duplicates=remove_duplicates,
            max_claims=max_claims,
        )
        progress.progress(100, text="Claims extracted.")
        progress.empty()

        if claim_error:
            logger.error(f"Claim extraction error: {claim_error}")
            st.error(f"Failed to extract claims: {claim_error}")
            return

        st.session_state.extracted_claims = claims
        st.session_state.verification_results = []
        logger.info(f"Successfully extracted {len(claims)} claims")
        st.success(f"Extracted {len(claims)} factual claims.")
    except Exception as exc:
        logger.exception(f"Unexpected error during extraction: {exc}")
        progress.empty()
        st.error(f"An unexpected error occurred: {exc}")


def verify_claims(model: str, min_confidence: int) -> None:
    logger.info("Starting verification workflow")
    claims = st.session_state.extracted_claims
    if not claims:
        logger.warning("No claims available for verification")
        st.warning("Extract claims before starting verification.")
        return

    logger.info(f"Verifying {len(claims)} claims with min_confidence={min_confidence}%")
    verifier = Verifier(model=model)
    progress = st.progress(0, text="Starting verification...")
    status = st.empty()

    def on_progress(current: int, total: int) -> None:
        percent = int((current / total) * 100) if total else 0
        progress.progress(percent, text=f"Verified {current} of {total} claims")
        status.caption(f"Checking claim {min(current + 1, total)} of {total}")

    try:
        results, error = verifier.verify_claims(
            claims,
            progress_callback=on_progress,
            min_confidence=min_confidence,
        )
        progress.progress(100, text="Verification complete.")
        status.empty()

        if error:
            logger.error(f"Verification error: {error}")
            st.error(f"Verification failed: {error}")
            return

        st.session_state.verification_results = results
        logger.info(f"Verification complete: {len(results)} claims passed filters")
        st.success(f"Verified {len(results)} claims.")
    except Exception as exc:
        logger.exception(f"Unexpected error during verification: {exc}")
        progress.empty()
        status.empty()
        st.error(f"An unexpected error occurred: {exc}")


def render_upload_section(uploaded_file, model: str, remove_duplicates: bool, max_claims: int) -> None:
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(248,250,252,0.8));
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid rgba(255,255,255,0.5);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
        margin-bottom: 2rem;
    '>
    <h3 style='margin-top: 0;'>📤 Upload & Process PDF</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if not uploaded_file:
        st.info("📁 Upload a PDF from the sidebar to begin your fact-checking journey.")
        return

    is_valid, error = validate_pdf_file(uploaded_file)
    if error:
        st.error(f"❌ {error}")
    else:
        size_mb = uploaded_file.size / (1024 * 1024)
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #dcfce7, #bbf7d0);
            border-left: 5px solid #10b981;
            padding: 1.25rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
        '>
        ✅ <b>File Selected:</b> <code>{uploaded_file.name}</code> ({size_mb:.2f} MB)
        </div>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**Ready to extract claims from your document?**")
    with col2:
        if st.button("🚀 Extract & Analyze", type="primary", use_container_width=True, disabled=not is_valid):
            extract_text_and_claims(uploaded_file, model, remove_duplicates, max_claims)

    metadata = st.session_state.document_metadata
    if metadata:
        st.markdown("---")
        st.markdown("### 📊 Document Analysis")
        col1, col2, col3 = st.columns(3, gap="large")
        
        with col1:
            st.metric("📄 Pages", metadata.get("pages", 0))
        with col2:
            st.metric("💾 File Size", f"{metadata.get('file_size_mb', 0):.2f} MB")
        with col3:
            char_count = len(st.session_state.extracted_text)
            st.metric("🔤 Characters", f"{char_count:,}" if char_count > 0 else "0")


def render_claims_section(model: str, min_confidence: int) -> None:
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(248,250,252,0.8));
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid rgba(255,255,255,0.5);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
        margin-bottom: 2rem;
    '>
    <h3 style='margin-top: 0;'>💬 Extracted Claims</h3>
    </div>
    """, unsafe_allow_html=True)
    
    claims = st.session_state.extracted_claims
    if not claims:
        st.info("✨ Claims will appear here after extraction.")
        return

    st.markdown(f"""
    <div style='
        background: linear-gradient(135deg, #dbeafe, #bfdbfe);
        border-left: 5px solid #3b82f6;
        padding: 1.25rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        font-weight: 600;
        color: #0c4a6e;
    '>
    🎯 Found <b>{len(claims)} factual claims</b> in your document
    </div>
    """, unsafe_allow_html=True)
    
    rows = [{"#": i, "Claim": c["claim"], "Type": c["type"], "Status": "⏳ Pending"} for i, c in enumerate(claims, 1)]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**Ready to verify these claims?** Click the button to start the verification process.")
    with col2:
        if st.button("✅ Begin Verification", type="primary", use_container_width=True):
            verify_claims(model, min_confidence)


def render_metrics(results: list[dict]) -> None:
    stats = calculate_claim_statistics(results)
    
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(248,250,252,0.8));
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid rgba(255,255,255,0.5);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
        margin-bottom: 2rem;
    '>
    <h3 style='margin-top: 0;'>📊 Verification Summary</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5, gap="small")
    
    with col1:
        st.metric("📊 Total", stats["total"], 
                 delta=f"{len(results)}" if results else None,
                 delta_color="normal")
    with col2:
        verified_pct = int(stats['verified']/stats['total']*100) if stats["total"] > 0 else 0
        st.metric("✅ Verified", stats["verified"], 
                 delta=f"{verified_pct}%")
    with col3:
        inaccurate_pct = int(stats['inaccurate']/stats['total']*100) if stats["total"] > 0 else 0
        st.metric("⚠️ Inaccurate", stats["inaccurate"],
                 delta=f"{inaccurate_pct}%")
    with col4:
        false_pct = int(stats['false']/stats['total']*100) if stats["total"] > 0 else 0
        st.metric("❌ False", stats["false"],
                 delta=f"{false_pct}%")
    with col5:
        st.metric("🎯 Avg Confidence", f"{stats['avg_confidence']}%", delta=None)


def render_report_section() -> None:
    st.subheader("📊 Verification Report")
    results = st.session_state.verification_results
    if not results:
        st.info("✨ Verification results will appear here after verification is complete.")
        return

    render_metrics(results)
    st.markdown("---")

    st.markdown("### 📋 Detailed Results")
    for index, result in enumerate(results, start=1):
        status = result.get("status", STATUS_UNVERIFIABLE)
        color = STATUS_COLORS.get(status, STATUS_COLORS[STATUS_UNVERIFIABLE])
        
        # Add emoji based on status
        status_emoji = {
            "Verified": "✅",
            "Inaccurate": "⚠️",
            "False": "❌",
            "Unverifiable": "❓"
        }.get(status, "❓")
        
        with st.expander(
            f"{status_emoji} {index}. {status} ({result.get('confidence', 0)}%) | {truncate_text(result.get('claim', ''), 80)}",
            expanded=index <= 2,
        ):
            st.markdown(
                f"""
                <div class='status-card {status.lower().replace(' ', '-')}'>
                <b>📌 Claim:</b> {escape(str(result.get('claim', '')))}<br>
                <b>🏷️ Type:</b> {escape(str(result.get('type', '')))}<br>
                <b>✓ Status:</b> <span style='color:{color}; font-weight:bold;'>{escape(str(status))}</span><br>
                <b>📈 Confidence:</b> {result.get('confidence', 0)}%<br>
                <b>💡 Explanation:</b> {escape(str(result.get('explanation', '')))}
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            col1, col2 = st.columns([1, 1], gap="large")
            
            with col1:
                if result.get("key_finding"):
                    st.markdown(f"**🔍 Key Finding:** {result['key_finding']}")
            
            with col2:
                if result.get("sources"):
                    st.markdown("**🔗 Sources:**")
                    for source in result["sources"]:
                        url = source.get('url', '')
                        title = source.get('title', 'Source')
                        if url:
                            st.markdown(f"- [{title}]({url})")
                        else:
                            st.markdown(f"- {title}")
            
            if result.get("evidence_snippet"):
                with st.popover("📄 View Evidence"):
                    st.text(result["evidence_snippet"])


def render_download_section() -> None:
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(248,250,252,0.8));
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid rgba(255,255,255,0.5);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
        margin-bottom: 2rem;
    '>
    <h3 style='margin-top: 0;'>📥 Download Reports</h3>
    </div>
    """, unsafe_allow_html=True)
    
    results = st.session_state.verification_results
    if not results:
        st.info("✨ Run verification to generate downloadable reports.")
        return

    logger.info(f"Preparing download section for {len(results)} verification results")
    generator = ReportGenerator()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    st.markdown("### 📊 Available Export Formats")
    
    col1, col2, col3 = st.columns(3, gap="medium")

    # CSV Report
    with col1:
        st.markdown("""
        <div style='
            background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(248,250,252,0.8));
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(226, 232, 240, 0.5);
            text-align: center;
        '>
        <h4 style='margin-top: 0;'>📋 CSV</h4>
        <p style='color: #64748b; font-size: 0.9rem; margin: 0.5rem 0;'>Spreadsheet compatible</p>
        """, unsafe_allow_html=True)
        
        csv_data, csv_error = generator.generate_csv_report(results)
        if csv_error:
            logger.error(f"CSV generation error: {csv_error}")
            st.error(f"❌ {csv_error}")
        else:
            st.download_button(
                "⬇️ Download CSV",
                data=csv_data,
                file_name=f"factcheck_report_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True,
                key="csv_download",
            )
            st.success("✅ Ready")
        st.markdown("</div>", unsafe_allow_html=True)

    # PDF Report
    with col2:
        st.markdown("""
        <div style='
            background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(248,250,252,0.8));
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(226, 232, 240, 0.5);
            text-align: center;
        '>
        <h4 style='margin-top: 0;'>📄 PDF</h4>
        <p style='color: #64748b; font-size: 0.9rem; margin: 0.5rem 0;'>Professional document</p>
        """, unsafe_allow_html=True)
        
        pdf_data, pdf_error = generator.generate_pdf_report(results)
        if pdf_error:
            logger.error(f"PDF generation error: {pdf_error}")
            st.error(f"❌ {pdf_error}")
        else:
            st.download_button(
                "⬇️ Download PDF",
                data=pdf_data,
                file_name=f"factcheck_report_{timestamp}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="pdf_download",
            )
            st.success("✅ Ready")
        st.markdown("</div>", unsafe_allow_html=True)

    # Markdown Report
    with col3:
        st.markdown("""
        <div style='
            background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(248,250,252,0.8));
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(226, 232, 240, 0.5);
            text-align: center;
        '>
        <h4 style='margin-top: 0;'>📝 Markdown</h4>
        <p style='color: #64748b; font-size: 0.9rem; margin: 0.5rem 0;'>Version control friendly</p>
        """, unsafe_allow_html=True)
        
        md_data, md_error = generator.generate_markdown_report(results)
        if md_error:
            logger.error(f"Markdown generation error: {md_error}")
            st.error(f"❌ {md_error}")
        else:
            st.download_button(
                "⬇️ Download Markdown",
                data=md_data,
                file_name=f"factcheck_report_{timestamp}.md",
                mime="text/markdown",
                use_container_width=True,
                key="md_download",
            )
            st.success("✅ Ready")
        st.markdown("</div>", unsafe_allow_html=True)

    if not (csv_error or pdf_error or md_error):
        logger.info("All reports generated successfully")
        st.markdown("---")
        st.success("🎉 All reports generated successfully!")


def main() -> None:
    init_state()

    # Modern Header with Glassmorphism
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(124, 58, 237, 0.1));
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 3rem 2rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    '>
    """, unsafe_allow_html=True)
    
    logo_path = BASE_DIR / "assets" / "logo.png"
    title_col, copy_col = st.columns([0.06, 0.94])
    
    with title_col:
        if logo_path.exists():
            st.image(str(logo_path), width=60)
    
    with copy_col:
        st.markdown(
            "<p class='app-title'>✨ FactCheck AI</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p class='muted'>🔍 Intelligent PDF Fact-Checking • Powered by OpenAI & Tavily Search</p>",
            unsafe_allow_html=True,
        )
    
    st.markdown("</div>", unsafe_allow_html=True)

    if not has_required_keys():
        st.error("❌ " + ERROR_API_KEY)
        st.stop()

    uploaded_file, model, remove_duplicates, max_claims, min_confidence = sidebar_controls()
    reset_for_new_file(uploaded_file)

    tab_upload, tab_claims, tab_report, tab_download = st.tabs([
        "📤 PDF Upload",
        "💬 Extracted Claims",
        "📊 Verification Report",
        "📥 Download Report",
    ])

    with tab_upload:
        render_upload_section(uploaded_file, model, remove_duplicates, max_claims)

    with tab_claims:
        render_claims_section(model, min_confidence)

    with tab_report:
        render_report_section()

    with tab_download:
        render_download_section()


if __name__ == "__main__":
    main()
