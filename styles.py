"""Shared CSS styles for Nexus Excel AI."""

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --nexus-bg-card: #1c2333;
    --nexus-border: #30363d;
    --nexus-text-muted: #8b949e;
    --nexus-text-primary: #e6edf3;
    --nexus-accent: #00d4aa;
    --nexus-accent-dim: rgba(0, 212, 170, 0.1);

    --bg-primary:    #0d1117;
    --bg-secondary:  #161b22;
    --bg-card:       var(--nexus-bg-card);
    --border:        var(--nexus-border);
    --text-primary:  var(--nexus-text-primary);
    --text-muted:    var(--nexus-text-muted);
    --accent:        var(--nexus-accent);
    --accent-dim:    var(--nexus-accent-dim);
    --danger:        #f85149;
    --warning:       #e3b341;
    --success:       #3fb950;
    --font-mono:     'Space Mono', monospace;
    --font-body:     'DM Sans', sans-serif;
}

@media (prefers-color-scheme: light) {
  :root {
    --nexus-bg-card: #f6f8fa;
    --nexus-border: #d0d7de;
    --nexus-text-muted: #57606a;
    --nexus-text-primary: #24292f;
    --nexus-accent: #0969da;
    --nexus-accent-dim: rgba(9, 105, 218, 0.1);

    --bg-primary:    #ffffff;
    --bg-secondary:  #f6f8fa;
    --bg-card:       var(--nexus-bg-card);
    --border:        var(--nexus-border);
    --text-primary:  var(--nexus-text-primary);
    --text-muted:    var(--nexus-text-muted);
    --accent:        var(--nexus-accent);
    --accent-dim:    var(--nexus-accent-dim);
    --danger:        #cf222e;
    --warning:       #9a6700;
    --success:       #1a7f37;
  }
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-body) !important;
}
[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
.block-container { padding: 2rem 2.5rem !important; max-width: 1200px; }
#MainMenu, footer, header { display: none !important; }

/* Hide auto sidebar nav, but keep toggle enabled */
[data-testid="stSidebarNavItems"] { display: none !important; }
[data-testid="stSidebarNavSeparator"] { display: none !important; }

/* Buttons */
.stButton > button {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: var(--font-body) !important;
    font-size: 0.875rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}
.stButton > button:active { transform: scale(0.97) !important; }

/* CTA accent button */
.cta-btn > button {
    background: linear-gradient(135deg, var(--nexus-accent), #0099ff) !important;
    color: var(--bg-primary) !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    border: none !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 20px var(--nexus-accent-dim) !important;
    transition: all 0.15s ease !important;
}
.cta-btn > button:hover {
    box-shadow: 0 6px 30px var(--nexus-accent-dim) !important;
    transform: translateY(-1px) !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: var(--font-body) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--nexus-accent-dim) !important;
}

/* Alerts */
[data-testid="stAlert"] { border-radius: 10px !important; border-left-width: 4px !important; }

/* Divider */
hr { border-color: var(--border) !important; }

/* Section label */
.section-label {
    font-family: var(--font-body);
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 1.5rem 0 0.75rem 0;
    padding-left: 8px;
    border-left: 3px solid var(--accent);
}

/* Download button */
[data-testid="stDownloadButton"] > button {
    background: var(--nexus-bg-card) !important;
    color: var(--success) !important;
    border: 1px solid var(--success) !important;
    border-radius: 8px !important;
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    border: 1px solid var(--border);
    overflow: hidden;
}

/* Status widget */
[data-testid="stStatusWidget"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}

/* File Uploader Custom Upgrade */
div[data-testid="stFileUploader"] {
    background: var(--nexus-bg-card);
    border: 2px dashed var(--nexus-border);
    border-radius: 12px;
    padding: 1.5rem;
    transition: border-color 0.2s ease;
}
div[data-testid="stFileUploader"]:hover {
    border-color: var(--nexus-accent);
}

/* Animations */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
.fade-up { animation: fadeUp 0.35s ease both; }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.3; }
}
.pulse-dot {
    width: 8px; height: 8px;
    background: var(--danger);
    border-radius: 50%;
    animation: pulse 1.2s infinite;
    display: inline-block;
}
</style>
"""

APP_CSS = """
<style>
/* Metric cards */
.metric-row { display: flex; gap: 1rem; margin: 1rem 0; flex-wrap: wrap; }
.metric-card {
    background: var(--nexus-bg-card);
    border: 1px solid var(--nexus-border);
    border-left: 3px solid var(--nexus-accent);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    cursor: default;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px var(--nexus-accent-dim);
}
.metric-card .label { font-size: 0.72rem; color: var(--nexus-text-muted); text-transform: uppercase; letter-spacing: 1px; }
.metric-card .value { font-family: var(--font-mono); font-size: 1.8rem; color: var(--nexus-text-primary); font-weight: 700; line-height: 1.2; }
.metric-card .sub   { font-size: 0.72rem; color: var(--nexus-text-muted); margin-top: 0.2rem; }
.metric-card .unit { font-size: 1rem; color: var(--nexus-text-muted); margin-left: 3px; vertical-align: baseline; }

/* Column pills */
.col-pills-wrap { max-height: 64px; overflow: hidden; margin: 0.5rem 0 1rem 0; transition: max-height 0.3s ease; }
.col-pills-wrap.expanded { max-height: 400px; }
.col-pill {
    display: inline-block;
    background: var(--bg-card);
    color: var(--text-muted);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 0.15rem 0.6rem;
    font-size: 0.72rem;
    font-family: var(--font-mono);
    margin: 0.15rem;
}

/* Results panel */
.results-panel {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    margin-top: 1rem;
}

/* Chart gallery */
.chart-gallery-item {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.75rem;
    margin-bottom: 0.75rem;
}
.chart-gallery-label { font-size: 0.72rem; color: var(--text-muted); font-family: var(--font-mono); margin-bottom: 0.5rem; }

/* Audit trail */
.audit-item {
    background: var(--bg-card);
    border-radius: 6px;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.4rem;
    font-size: 0.875rem;
    color: var(--text-muted);
    border-left: 2px solid var(--border);
}
.audit-item .audit-cmd { color: var(--text-primary); font-size: 0.875rem; margin-bottom: 2px; }
.audit-item .audit-meta { font-size: 0.72rem; color: var(--text-muted); display: flex; gap: 0.5rem; align-items: center; }
.audit-badge-ok  { background: #3fb95022; color: var(--success); border-radius: 4px; padding: 1px 6px; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; }
.audit-badge-err { background: #f8514922; color: var(--danger);  border-radius: 4px; padding: 1px 6px; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; }

/* Recording */
.recording-indicator { display: flex; align-items: center; gap: 0.4rem; font-size: 0.8rem; color: var(--danger); margin-top: 0.3rem; }

/* Rate limit */
.rate-limit-badge { font-size: 0.72rem; color: var(--warning); font-family: var(--font-mono); text-align: right; margin-top: 0.3rem; }

/* Sidebar brand */
.sidebar-brand { text-align: center; padding: 1rem 0 1.5rem 0; border-bottom: 1px solid var(--border); margin-bottom: 1rem; }
.sidebar-brand .logo { font-family: var(--font-mono); font-size: 1.5rem; color: var(--accent); font-weight: 700; letter-spacing: 2px; }
.sidebar-brand .tagline { font-size: 0.72rem; color: var(--text-muted); letter-spacing: 1px; text-transform: uppercase; }

/* Hero */
.hero-zone { padding: 1.5rem 0 1rem 0; border-bottom: 1px solid var(--border); margin-bottom: 1.5rem; }
.hero-title { font-family: var(--font-mono); font-size: 2rem; color: var(--accent); letter-spacing: -1px; margin: 0; }
.hero-sub { color: var(--text-muted); font-size: 0.875rem; margin-top: 0.3rem; }

/* Feature-gate banner */
.gate-banner {
    background: #e3b34115;
    border: 1px solid #e3b34140;
    border-radius: 10px;
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    color: var(--warning);
    margin: 0.5rem 0 1rem 0;
    display: flex; align-items: center; gap: 0.5rem;
}

@media (max-width: 900px) {
    .metric-row { flex-wrap: wrap; }
    .metric-card { min-width: 120px; }
    .hero-title { font-size: 1.4rem; }
}
</style>
"""
