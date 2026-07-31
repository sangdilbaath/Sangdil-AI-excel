"""Shared CSS styles for Nexus Excel AI."""

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600;700&display=swap');

:root {
    --nexus-bg-card: rgba(28, 35, 51, 0.6);
    --nexus-border: rgba(48, 54, 61, 0.5);
    --nexus-text-muted: #8b949e;
    --nexus-text-primary: #e6edf3;
    --nexus-accent: #00e5ff;
    --nexus-accent-dim: rgba(0, 229, 255, 0.15);
    --nexus-backdrop-blur: blur(16px);

    --bg-primary:    #050810;
    --bg-secondary:  #0a101b;
    --bg-card:       var(--nexus-bg-card);
    --border:        var(--nexus-border);
    --text-primary:  var(--nexus-text-primary);
    --text-muted:    var(--nexus-text-muted);
    --accent:        var(--nexus-accent);
    --accent-dim:    var(--nexus-accent-dim);
    --danger:        #ff4a4a;
    --warning:       #ffb84d;
    --success:       #00e676;
    --font-mono:     'Space Mono', monospace;
    --font-body:     'DM Sans', sans-serif;
}

@media (prefers-color-scheme: light) {
  :root {
    --nexus-bg-card: rgba(255, 255, 255, 0.7);
    --nexus-border: rgba(208, 215, 222, 0.5);
    --nexus-text-muted: #57606a;
    --nexus-text-primary: #1f2328;
    --nexus-accent: #005cc5;
    --nexus-accent-dim: rgba(0, 92, 197, 0.1);

    --bg-primary:    #f6f8fa;
    --bg-secondary:  #ffffff;
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
    backdrop-filter: var(--nexus-backdrop-blur);
    -webkit-backdrop-filter: var(--nexus-backdrop-blur);
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
.block-container { padding: 3rem 4rem !important; max-width: 1300px; }
#MainMenu, footer, header { display: none !important; }

/* Hide auto sidebar nav, but keep toggle enabled */
[data-testid="stSidebarNavItems"] { display: none !important; }
[data-testid="stSidebarNavSeparator"] { display: none !important; }

/* Buttons */
.stButton > button {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: var(--font-body) !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    backdrop-filter: var(--nexus-backdrop-blur);
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: var(--accent-dim) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: scale(0.97) !important; }

/* CTA accent button */
.cta-btn > button {
    background: linear-gradient(135deg, var(--accent), #0088ff) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    border: none !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 20px var(--accent-dim) !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.cta-btn > button:hover {
    box-shadow: 0 8px 30px rgba(0, 229, 255, 0.3) !important;
    transform: translateY(-2px) !important;
}
.cta-btn > button:active { transform: translateY(0) scale(0.98) !important; }

/* Action Toolkit Buttons */
.action-btn > button {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
}
.action-btn > button:hover {
    background: var(--accent-dim) !important;
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    font-family: var(--font-body) !important;
    backdrop-filter: var(--nexus-backdrop-blur);
    transition: all 0.2s ease !important;
    padding: 0.75rem 1rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-dim) !important;
    background: rgba(0, 0, 0, 0.4) !important;
}

/* Alerts */
[data-testid="stAlert"] { 
    border-radius: 12px !important; 
    border-left-width: 4px !important; 
    background: var(--bg-card) !important;
    backdrop-filter: var(--nexus-backdrop-blur);
}

/* Divider */
hr { border-color: var(--border) !important; opacity: 0.5; }

/* Section label */
.section-label {
    font-family: var(--font-body);
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 2.5px;
    margin: 2rem 0 1rem 0;
    padding-left: 12px;
    border-left: 3px solid var(--accent);
    font-weight: 600;
}

/* Download button */
[data-testid="stDownloadButton"] > button {
    background: var(--bg-card) !important;
    color: var(--success) !important;
    border: 1px solid var(--success) !important;
    border-radius: 10px !important;
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: rgba(0, 230, 118, 0.1) !important;
    box-shadow: 0 4px 15px rgba(0, 230, 118, 0.15) !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    border: 1px solid var(--border);
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}

/* Status widget */
[data-testid="stStatusWidget"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    backdrop-filter: var(--nexus-backdrop-blur);
}

/* File Uploader Custom Upgrade */
div[data-testid="stFileUploader"] {
    background: var(--bg-card);
    border: 2px dashed var(--nexus-border);
    border-radius: 16px;
    padding: 2rem;
    transition: all 0.3s ease;
    backdrop-filter: var(--nexus-backdrop-blur);
}
div[data-testid="stFileUploader"]:hover {
    border-color: var(--accent);
    background: var(--accent-dim);
    transform: translateY(-2px);
}

/* Tabs */
[data-baseweb="tab"] {
    font-family: var(--font-body) !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    padding: 1rem 1.5rem !important;
}
[data-baseweb="tab-highlight"] {
    background-color: var(--accent) !important;
}
[data-baseweb="tab-list"] {
    gap: 1rem !important;
    border-bottom-color: var(--border) !important;
}

/* Animations */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
.fade-up { animation: fadeUp 0.4s cubic-bezier(0.4, 0, 0.2, 1) both; }

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.5; transform: scale(1.1); }
}
.pulse-dot {
    width: 10px; height: 10px;
    background: var(--accent);
    border-radius: 50%;
    animation: pulse 1.5s infinite;
    display: inline-block;
    box-shadow: 0 0 10px var(--accent);
}
</style>
"""

APP_CSS = """
<style>
/* Metric cards */
.metric-row { display: flex; gap: 1.25rem; margin: 1.5rem 0; flex-wrap: wrap; }
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    cursor: default;
    flex: 1;
    min-width: 180px;
    backdrop-filter: var(--nexus-backdrop-blur);
}
.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px var(--accent-dim);
}
.metric-card .label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600; }
.metric-card .value { font-family: var(--font-mono); font-size: 2rem; color: var(--text-primary); font-weight: 700; line-height: 1.3; margin: 0.25rem 0; }
.metric-card .sub   { font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem; }
.metric-card .unit { font-size: 1.1rem; color: var(--text-muted); margin-left: 4px; vertical-align: baseline; font-weight: 400; }

/* Column pills */
.col-pills-wrap { max-height: 64px; overflow: hidden; margin: 1rem 0 1.5rem 0; transition: max-height 0.4s ease; display: flex; flex-wrap: wrap; gap: 0.5rem; }
.col-pills-wrap.expanded { max-height: 500px; }
.col-pill {
    display: inline-flex;
    align-items: center;
    background: rgba(255,255,255,0.03);
    color: var(--text-primary);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 0.3rem 0.8rem;
    font-size: 0.75rem;
    font-family: var(--font-mono);
    backdrop-filter: var(--nexus-backdrop-blur);
}
.col-pill:hover {
    border-color: var(--accent);
    background: var(--accent-dim);
}

/* Results panel */
.results-panel {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.75rem;
    margin-top: 1.5rem;
    backdrop-filter: var(--nexus-backdrop-blur);
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

/* Chart gallery */
.chart-gallery-item {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
    backdrop-filter: var(--nexus-backdrop-blur);
}
.chart-gallery-label { font-size: 0.8rem; color: var(--text-muted); font-family: var(--font-mono); margin-bottom: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }

/* Audit trail */
.audit-item {
    background: var(--bg-card);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    color: var(--text-muted);
    border-left: 3px solid var(--border);
    backdrop-filter: var(--nexus-backdrop-blur);
}
.audit-item:hover { border-left-color: var(--accent); }
.audit-item .audit-cmd { color: var(--text-primary); font-size: 0.95rem; margin-bottom: 4px; font-weight: 500; }
.audit-item .audit-meta { font-size: 0.75rem; color: var(--text-muted); display: flex; gap: 0.75rem; align-items: center; font-family: var(--font-mono); }
.audit-badge-ok  { background: rgba(0, 230, 118, 0.15); color: var(--success); border-radius: 6px; padding: 2px 8px; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; }
.audit-badge-err { background: rgba(255, 74, 74, 0.15); color: var(--danger);  border-radius: 6px; padding: 2px 8px; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; }

/* Recording */
.recording-indicator { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; color: var(--danger); margin-top: 0.5rem; font-weight: 600; }

/* Rate limit */
.rate-limit-badge { font-size: 0.75rem; color: var(--warning); font-family: var(--font-mono); text-align: right; margin-top: 0.5rem; font-weight: 600; }

/* Sidebar brand */
.sidebar-brand { text-align: center; padding: 1.5rem 0 2rem 0; border-bottom: 1px solid var(--border); margin-bottom: 1.5rem; }
.sidebar-brand .logo { font-family: var(--font-mono); font-size: 1.75rem; color: var(--text-primary); font-weight: 700; letter-spacing: 3px; }
.sidebar-brand .logo span { color: var(--accent); }
.sidebar-brand .tagline { font-size: 0.75rem; color: var(--text-muted); letter-spacing: 2px; text-transform: uppercase; margin-top: 0.5rem; }

/* Hero */
.hero-zone { padding: 2.5rem 0 1.5rem 0; border-bottom: 1px solid var(--border); margin-bottom: 2rem; display: flex; flex-direction: column; align-items: center; text-align: center; }
.hero-title { font-family: var(--font-mono); font-size: 2.75rem; color: var(--text-primary); letter-spacing: -1px; margin: 0; font-weight: 700; }
.hero-title span { color: var(--accent); }
.hero-sub { color: var(--text-muted); font-size: 1rem; margin-top: 0.75rem; font-weight: 400; max-width: 600px; }

/* Feature-gate banner */
.gate-banner {
    background: rgba(255, 184, 77, 0.1);
    border: 1px solid rgba(255, 184, 77, 0.3);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    font-size: 0.9rem;
    color: var(--warning);
    margin: 1rem 0 1.5rem 0;
    display: flex; align-items: center; gap: 0.75rem;
    font-weight: 500;
}

@media (max-width: 900px) {
    .metric-row { flex-wrap: wrap; }
    .metric-card { min-width: 140px; }
    .hero-title { font-size: 2rem; }
    .block-container { padding: 1.5rem !important; }
}
</style>
"""

