"""PPT-aligned Streamlit theme styles."""

PPT_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
    --brand: #3B4FBF;
    --brand-dark: #2f3f9c;
    --brand-light: #eef2ff;
    --verified: #059669;
    --verified-bg: #ecfdf5;
    --inaccurate: #d97706;
    --inaccurate-bg: #fffbeb;
    --false: #dc2626;
    --false-bg: #fef2f2;
    --muted: #64748b;
    --border: #e2e8f0;
    --card: #ffffff;
    --surface: #f8fafc;
}

html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

.block-container {
    padding-top: 1.5rem !important;
    max-width: 1320px !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
    border-right: 1px solid var(--border);
}

.hero-wrap {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 45%, #3B4FBF 100%);
    border-radius: 20px;
    padding: 2.5rem 2rem;
    color: white;
    margin-bottom: 1.5rem;
    box-shadow: 0 20px 50px rgba(59, 79, 191, 0.25);
}

.hero-kicker {
    font-size: 0.85rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    opacity: 0.85;
    margin-bottom: 0.35rem;
}

.hero-title {
    font-size: 3rem;
    font-weight: 900;
    line-height: 1.05;
    margin: 0;
}

.hero-subtitle {
    font-size: 1.05rem;
    opacity: 0.92;
    margin-top: 0.75rem;
}

.hero-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    margin-top: 1.25rem;
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.45rem 0.85rem;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 700;
    border: 1px solid rgba(255,255,255,0.18);
    background: rgba(255,255,255,0.1);
}

.badge.verified { color: #6ee7b7; }
.badge.inaccurate { color: #fcd34d; }
.badge.false { color: #fca5a5; }

.hero-footer {
    margin-top: 1.25rem;
    font-size: 0.82rem;
    opacity: 0.75;
}

.section-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.25rem 1.35rem;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
    margin-bottom: 1rem;
}

.section-title {
    font-size: 1.05rem;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 0.35rem 0;
}

.section-desc {
    color: var(--muted);
    font-size: 0.92rem;
    margin: 0 0 1rem 0;
}

.upload-dropzone {
    border: 2px dashed #c7d2fe;
    background: linear-gradient(180deg, #ffffff, #f8fafc);
    border-radius: 14px;
    padding: 1.5rem;
    text-align: center;
}

.workflow-grid {
    display: grid;
    grid-template-columns: repeat(8, minmax(0, 1fr));
    gap: 0.45rem;
    margin: 0.5rem 0 1rem 0;
}

@media (max-width: 1100px) {
    .workflow-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}

.workflow-step {
    background: #f8fafc;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.65rem 0.5rem;
    text-align: center;
    min-height: 78px;
}

.workflow-step.active {
    background: var(--brand-light);
    border-color: #c7d2fe;
    box-shadow: 0 0 0 2px rgba(59, 79, 191, 0.12);
}

.workflow-step.done {
    background: #ecfdf5;
    border-color: #a7f3d0;
}

.workflow-num {
    font-size: 0.72rem;
    font-weight: 800;
    color: var(--brand);
}

.workflow-label {
    font-size: 0.72rem;
    color: #334155;
    font-weight: 600;
    line-height: 1.25;
    margin-top: 0.25rem;
}

.summary-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.75rem;
}

.summary-tile {
    border-radius: 14px;
    padding: 1rem;
    border: 1px solid var(--border);
    background: #fff;
}

.summary-tile.total { border-left: 4px solid var(--brand); }
.summary-tile.verified { border-left: 4px solid var(--verified); background: var(--verified-bg); }
.summary-tile.inaccurate { border-left: 4px solid var(--inaccurate); background: var(--inaccurate-bg); }
.summary-tile.false { border-left: 4px solid var(--false); background: var(--false-bg); }

.summary-label {
    font-size: 0.78rem;
    color: var(--muted);
    font-weight: 600;
}

.summary-value {
    font-size: 1.8rem;
    font-weight: 900;
    color: #0f172a;
    line-height: 1.1;
}

.result-card {
    border-radius: 14px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.75rem;
    border: 1px solid var(--border);
}

.result-card.verified {
    background: var(--verified-bg);
    border-left: 5px solid var(--verified);
}

.result-card.inaccurate {
    background: var(--inaccurate-bg);
    border-left: 5px solid var(--inaccurate);
}

.result-card.false {
    background: var(--false-bg);
    border-left: 5px solid var(--false);
}

.result-card.unverifiable {
    background: #f8fafc;
    border-left: 5px solid #94a3b8;
}

.result-status {
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.result-claim {
    font-size: 0.98rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0.35rem 0;
}

.result-meta {
    font-size: 0.86rem;
    color: var(--muted);
}

.review-flag {
    display: inline-block;
    margin-top: 0.45rem;
    padding: 0.25rem 0.55rem;
    border-radius: 999px;
    background: #fef3c7;
    color: #92400e;
    font-size: 0.75rem;
    font-weight: 700;
}

.report-card {
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.25rem;
    height: 100%;
}

.report-card h4 {
    margin: 0 0 0.35rem 0;
    color: #0f172a;
}

.report-card ul {
    margin: 0.5rem 0 0 1rem;
    padding: 0;
    color: var(--muted);
    font-size: 0.88rem;
}

.report-audience {
    margin-top: 0.75rem;
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--brand);
}

.info-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
}

@media (max-width: 900px) {
    .info-grid { grid-template-columns: 1fr; }
}

.info-tile {
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1rem;
}

.info-tile h5 {
    margin: 0 0 0.35rem 0;
    color: #0f172a;
}

.info-tile p {
    margin: 0;
    color: var(--muted);
    font-size: 0.88rem;
}

button[kind="primary"] {
    background: linear-gradient(135deg, var(--brand), var(--brand-dark)) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
}

.stTabs [aria-selected="true"] {
    background: var(--brand) !important;
    color: white !important;
    border-radius: 8px !important;
}
</style>
"""
