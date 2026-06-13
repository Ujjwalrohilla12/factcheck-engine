"""Professional Streamlit theme for FactCheck AI."""

PPT_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ── Variables ── */
:root {
    --brand:          #4F46E5;
    --brand-dark:     #3730A3;
    --brand-mid:      #6366F1;
    --brand-light:    #EEF2FF;
    --brand-glow:     rgba(79, 70, 229, 0.15);
    --verified:       #059669;
    --verified-bg:    #ECFDF5;
    --verified-border:#A7F3D0;
    --inaccurate:     #D97706;
    --inaccurate-bg:  #FFFBEB;
    --inaccurate-border:#FDE68A;
    --false:          #DC2626;
    --false-bg:       #FEF2F2;
    --false-border:   #FECACA;
    --unverifiable:   #64748B;
    --unverifiable-bg:#F8FAFC;
    --muted:          #64748B;
    --muted-light:    #94A3B8;
    --border:         #E2E8F0;
    --border-strong:  #CBD5E1;
    --card:           #FFFFFF;
    --surface:        #F8FAFC;
    --surface-2:      #F1F5F9;
    --text:           #0F172A;
    --text-secondary: #334155;
    --shadow-sm:      0 1px 3px rgba(15,23,42,0.08), 0 1px 2px rgba(15,23,42,0.06);
    --shadow-md:      0 4px 16px rgba(15,23,42,0.08), 0 2px 4px rgba(15,23,42,0.05);
    --shadow-lg:      0 10px 40px rgba(15,23,42,0.10), 0 4px 8px rgba(15,23,42,0.06);
    --radius-sm:      8px;
    --radius-md:      12px;
    --radius-lg:      16px;
    --radius-xl:      20px;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    -webkit-font-smoothing: antialiased;
}

.block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 2rem !important;
    max-width: 1380px !important;
}

/* Hide Streamlit default header decoration */
header[data-testid="stHeader"] { background: transparent !important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid var(--border) !important;
    box-shadow: 2px 0 12px rgba(15,23,42,0.04) !important;
}

section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
}

/* Sidebar brand block */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 1.2rem 1rem 0.8rem 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}

.sidebar-logo {
    font-size: 1.6rem;
    line-height: 1;
    background: linear-gradient(135deg, var(--brand), var(--brand-mid));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.sidebar-title {
    font-size: 0.95rem;
    font-weight: 800;
    color: var(--text);
    line-height: 1.2;
}

.sidebar-sub {
    font-size: 0.72rem;
    color: var(--muted);
    font-weight: 500;
    letter-spacing: 0.02em;
}

/* API status pill */
.api-status {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    padding: 0.3rem 0.75rem;
    border-radius: 999px;
    margin: 0 0 0.75rem 0;
    width: fit-content;
}

.api-status.ok {
    background: var(--verified-bg);
    color: var(--verified);
    border: 1px solid var(--verified-border);
}

.api-status.warn {
    background: var(--false-bg);
    color: var(--false);
    border: 1px solid var(--false-border);
}

/* Sidebar section labels */
.sidebar-section-label {
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    color: var(--muted-light);
    text-transform: uppercase;
    padding: 0.6rem 0 0.3rem 0;
    margin-top: 0.25rem;
}

/* Demo badge */
.demo-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--brand);
    background: var(--brand-light);
    border: 1px solid #C7D2FE;
    padding: 0.3rem 0.7rem;
    border-radius: 999px;
    margin-top: 0.5rem;
}

/* ── Hero ── */
.hero-wrap {
    background: linear-gradient(135deg, #1E1B4B 0%, #312E81 40%, #4F46E5 75%, #6366F1 100%);
    border-radius: var(--radius-xl);
    padding: 2.8rem 2.5rem 2.2rem;
    color: white;
    margin-bottom: 1.5rem;
    box-shadow: 0 24px 60px rgba(79, 70, 229, 0.3), 0 8px 20px rgba(79, 70, 229, 0.2);
    position: relative;
    overflow: hidden;
}

.hero-wrap::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(255,255,255,0.06) 0%, transparent 70%);
    border-radius: 50%;
}

.hero-wrap::after {
    content: '';
    position: absolute;
    bottom: -80px; left: 30%;
    width: 350px; height: 350px;
    background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
    border-radius: 50%;
}

.hero-kicker {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    opacity: 0.7;
    margin-bottom: 0.5rem;
}

.hero-title {
    font-size: 3.2rem;
    font-weight: 900;
    line-height: 1.0;
    letter-spacing: -0.02em;
    margin: 0;
}

.hero-subtitle {
    font-size: 1.05rem;
    opacity: 0.85;
    font-weight: 400;
    margin-top: 0.65rem;
    max-width: 480px;
}

.hero-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin-top: 1.4rem;
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.38rem 0.85rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.2);
    background: rgba(255,255,255,0.12);
    transition: background 0.2s;
}

.badge.verified   { color: #6EE7B7; }
.badge.inaccurate { color: #FCD34D; }
.badge.false      { color: #FCA5A5; }

.hero-footer {
    margin-top: 1.4rem;
    font-size: 0.76rem;
    opacity: 0.55;
    font-weight: 400;
    position: relative;
    z-index: 1;
}

/* ── Banner (warning) ── */
.banner-warn {
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-left: 4px solid #F59E0B;
    border-radius: var(--radius-md);
    padding: 0.85rem 1.1rem;
    font-size: 0.88rem;
    color: #78350F;
    margin-bottom: 1rem;
    line-height: 1.5;
}

.banner-warn code {
    background: rgba(245,158,11,0.12);
    padding: 0.1rem 0.35rem;
    border-radius: 4px;
    font-size: 0.82rem;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

/* ── Section cards ── */
.section-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.3rem 1.5rem;
    box-shadow: var(--shadow-sm);
    margin-bottom: 1rem;
}

.section-title {
    font-size: 1rem;
    font-weight: 800;
    color: var(--text);
    margin: 0 0 0.25rem 0;
    letter-spacing: -0.01em;
}

.section-desc {
    color: var(--muted);
    font-size: 0.87rem;
    margin: 0 0 0.9rem 0;
    line-height: 1.5;
}

/* ── Upload dropzone ── */
.upload-dropzone {
    border: 2px dashed #C7D2FE;
    background: linear-gradient(160deg, #FAFBFF, #F5F3FF);
    border-radius: var(--radius-md);
    padding: 1.6rem;
    text-align: center;
    color: var(--muted);
    font-size: 0.88rem;
    line-height: 1.6;
    transition: border-color 0.2s, background 0.2s;
}

/* ── Workflow steps ── */
.workflow-grid {
    display: grid;
    grid-template-columns: repeat(8, minmax(0, 1fr));
    gap: 0.4rem;
    margin: 0.6rem 0 1.2rem 0;
}

@media (max-width: 1100px) {
    .workflow-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}

.workflow-step {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 0.7rem 0.5rem;
    text-align: center;
    min-height: 76px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
}

.workflow-step.active {
    background: var(--brand-light);
    border-color: #A5B4FC;
    box-shadow: 0 0 0 3px var(--brand-glow);
    transform: translateY(-1px);
}

.workflow-step.done {
    background: var(--verified-bg);
    border-color: var(--verified-border);
}

.workflow-num {
    font-size: 0.65rem;
    font-weight: 900;
    color: var(--brand);
    letter-spacing: 0.05em;
}

.workflow-step.done .workflow-num { color: var(--verified); }

.workflow-label {
    font-size: 0.68rem;
    color: var(--text-secondary);
    font-weight: 600;
    line-height: 1.3;
    margin-top: 0.3rem;
}

/* ── Summary tiles ── */
.summary-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.7rem;
}

.summary-tile {
    border-radius: var(--radius-md);
    padding: 1rem 1.1rem;
    border: 1px solid var(--border);
    background: #FFF;
    transition: transform 0.15s;
}

.summary-tile:hover { transform: translateY(-1px); }
.summary-tile.total    { border-left: 4px solid var(--brand); }
.summary-tile.verified { border-left: 4px solid var(--verified); background: var(--verified-bg); border-color: var(--verified-border); }
.summary-tile.inaccurate { border-left: 4px solid var(--inaccurate); background: var(--inaccurate-bg); border-color: var(--inaccurate-border); }
.summary-tile.false    { border-left: 4px solid var(--false); background: var(--false-bg); border-color: var(--false-border); }

.summary-label {
    font-size: 0.72rem;
    color: var(--muted);
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.summary-value {
    font-size: 2rem;
    font-weight: 900;
    color: var(--text);
    line-height: 1.1;
    margin-top: 0.2rem;
    letter-spacing: -0.02em;
}

/* ── Result cards ── */
.result-card {
    border-radius: var(--radius-md);
    padding: 1rem 1.15rem;
    margin-bottom: 0.65rem;
    border: 1px solid var(--border);
    transition: box-shadow 0.15s;
}

.result-card:hover { box-shadow: var(--shadow-md); }

.result-card.verified    { background: var(--verified-bg);    border-left: 4px solid var(--verified);    border-color: var(--verified-border); }
.result-card.inaccurate  { background: var(--inaccurate-bg);  border-left: 4px solid var(--inaccurate);  border-color: var(--inaccurate-border); }
.result-card.false       { background: var(--false-bg);       border-left: 4px solid var(--false);       border-color: var(--false-border); }
.result-card.unverifiable{ background: var(--unverifiable-bg);border-left: 4px solid var(--unverifiable);border-color: var(--border-strong); }

.result-status {
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}

.result-claim {
    font-size: 0.92rem;
    font-weight: 600;
    color: var(--text);
    margin: 0.3rem 0;
    line-height: 1.45;
}

.result-meta {
    font-size: 0.8rem;
    color: var(--muted);
    font-weight: 500;
}

/* ── Review flag ── */
.review-flag {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    margin-top: 0.4rem;
    padding: 0.22rem 0.6rem;
    border-radius: 999px;
    background: #FEF3C7;
    color: #92400E;
    font-size: 0.72rem;
    font-weight: 700;
    border: 1px solid #FDE68A;
}

/* ── Report cards ── */
.report-card {
    background: #FFF;
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.3rem 1.3rem 1.1rem;
    height: 100%;
    transition: box-shadow 0.15s, transform 0.15s;
}

.report-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

.report-card h4 {
    margin: 0 0 0.4rem 0;
    color: var(--text);
    font-size: 0.95rem;
    font-weight: 800;
}

.report-card ul {
    margin: 0.5rem 0 0 1.1rem;
    padding: 0;
    color: var(--muted);
    font-size: 0.83rem;
    line-height: 1.7;
}

.report-audience {
    margin-top: 0.8rem;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    color: var(--brand);
    text-transform: uppercase;
}

/* ── Info grid (About tab) ── */
.info-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
}

@media (max-width: 900px) { .info-grid { grid-template-columns: 1fr; } }

.info-tile {
    background: #FFF;
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1.1rem;
    transition: box-shadow 0.15s;
}

.info-tile:hover { box-shadow: var(--shadow-sm); }

.info-tile h5 {
    margin: 0 0 0.35rem 0;
    color: var(--text);
    font-size: 0.88rem;
    font-weight: 700;
}

.info-tile p {
    margin: 0;
    color: var(--muted);
    font-size: 0.83rem;
    line-height: 1.5;
}

/* ── Streamlit widget overrides ── */
/* Primary buttons */
div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stButton"] > button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, var(--brand) 0%, var(--brand-mid) 100%) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 700 !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 4px 12px rgba(79,70,229,0.3) !important;
    transition: box-shadow 0.2s, transform 0.1s !important;
}

div[data-testid="stButton"] > button[kind="primary"]:hover {
    box-shadow: 0 6px 18px rgba(79,70,229,0.4) !important;
    transform: translateY(-1px) !important;
}

/* Secondary buttons */
div[data-testid="stButton"] > button[kind="secondary"] {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    border-color: var(--border-strong) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.25rem;
    background: var(--surface-2);
    padding: 0.3rem;
    border-radius: var(--radius-md);
    border: 1px solid var(--border);
}

.stTabs [data-baseweb="tab"] {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.4rem 1rem !important;
    color: var(--muted) !important;
    transition: all 0.15s !important;
}

.stTabs [aria-selected="true"] {
    background: var(--brand) !important;
    color: white !important;
    box-shadow: 0 2px 8px rgba(79,70,229,0.3) !important;
}

/* Metrics */
div[data-testid="stMetric"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 0.8rem 1rem;
    box-shadow: var(--shadow-sm);
}

/* Dataframe */
div[data-testid="stDataFrame"] {
    border-radius: var(--radius-md) !important;
    overflow: hidden;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-sm);
}

/* Progress bar */
div[data-testid="stProgressBar"] > div > div > div {
    background: linear-gradient(90deg, var(--brand), var(--brand-mid)) !important;
    border-radius: 999px !important;
}

/* Expander */
details[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-sm) !important;
    margin-bottom: 0.5rem !important;
}

details[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.75rem 1rem !important;
}

/* File uploader */
div[data-testid="stFileUploader"] {
    border-radius: var(--radius-md) !important;
}

/* Select box */
div[data-testid="stSelectbox"] > div > div {
    border-radius: var(--radius-sm) !important;
    border-color: var(--border-strong) !important;
}

/* Sidebar toggle/slider labels */
section[data-testid="stSidebar"] label {
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--text-secondary) !important;
}

/* Success / info / warning / error boxes */
div[data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
}
</style>
"""
