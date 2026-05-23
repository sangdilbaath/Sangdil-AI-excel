"""
pages/3_App.py — Nexus Excel AI · Main AI Dashboard
Access-controlled AI data analyst powered by Nexus.
"""

import streamlit as st
import sys, os, re, io, time, datetime, concurrent.futures, traceback, json
import multiprocessing
import contextlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    sns = None
    SEABORN_AVAILABLE = False

# Try importing mic-recorder gracefully
try:
    from streamlit_mic_recorder import mic_recorder
    VOICE_COMMAND_SUPPORT = True
except ImportError:
    VOICE_COMMAND_SUPPORT = False

from database import is_account_expired, days_remaining, PLAN_LABELS
from styles import GLOBAL_CSS, APP_CSS

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus Excel AI — Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown(APP_CSS,    unsafe_allow_html=True)

# ============================================================
# ACCESS CONTROL
# ============================================================
is_admin = st.session_state.get("is_admin", False)
user = st.session_state.get("user")

if not user:
    st.switch_page("Home.py")

if is_admin:
    plan = "pro"
    account_exp = False
else:
    from database import get_user
    email = st.session_state.get("email", user.get("email", ""))
    if email:
        fresh = get_user(email)
        if fresh:
            user = fresh
            st.session_state["user"] = fresh

    if not user.get("has_payment_on_file"):
        st.switch_page("pages/1_Start_Trial.py")

    plan        = user.get("plan_type", "none")
    account_exp = is_account_expired(user)

# ── Universal Expiry Wall ─────────────────────────────────────
if account_exp:
    st.markdown("""
    <div style="text-align:center; padding:5rem 1rem;">
        <div style="font-size:3rem;">⏰</div>
        <h2 style="font-family:'Space Mono',monospace; color:var(--nexus-text-primary); margin:1rem 0 0.5rem 0;">
            Your access has expired.
        </h2>
        <p style="color:var(--nexus-text-muted); font-size:1rem; max-width:460px; margin:0 auto 2rem auto;">
            Please contact the administrator to renew your plan.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ============================================================
# CONSTANTS
# ============================================================
MAX_FILE_SIZE_MB         = 10
MAX_REQUESTS_PER_SESSION = 99999 if is_admin else 50
AI_TIMEOUT_SECONDS       = 30
PYTHON_KEYWORDS          = {'import', 'def', 'df', 'plt', 'pd', 'for', 'if', 'print', 'return', '=', 'fig', 'ax'}

# ============================================================
# SESSION STATE
# ============================================================
for key, default in {
    "query_text":      "",
    "updated_df":      None,
    "chart_gallery":   [],
    "command_history": [],
    "chat_history":    [],
    "df":              None,
    "last_filename":   None,
    "show_all_data":   False,
    "show_all_cols":   False,
    "request_count":   0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ============================================================
# ISOLATED WORKER & HELPERS
# ============================================================
def _secure_sandbox_worker(code: str, df: pd.DataFrame, response_queue: multiprocessing.Queue):
    """
    Runs within an entirely separate OS process. This completely prevents thread cross-contamination,
    isolates sys.stdout mutations, and strips visibility into the main server's environment and memory space.
    """
    import io
    import sys
    import pandas as pd
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')  # Guarantee non-interactive headless rendering
    import matplotlib.pyplot as plt
    try:
        import seaborn as sns
    except ImportError:
        sns = None

    stdout_capture = io.StringIO()
    
    # Establish a highly constrained execution context with zero external namespaces
    sandbox_builtins = {
        'print': print, 'range': range, 'len': len, 'int': int, 'float': float, 
        'str': str, 'list': list, 'dict': dict, 'set': set, 'tuple': tuple, 
        'round': round, 'sum': sum, 'min': min, 'max': max, 'abs': abs,
        'enumerate': enumerate, 'zip': zip, 'bool': bool, 'isinstance': isinstance
    }
    
    exec_globals = {
        "pd": pd,
        "np": np,
        "plt": plt,
        "sns": sns,
        "df": df,
        "__builtins__": sandbox_builtins
    }
    
    try:
        # Guarantee clean canvas separation for plots
        plt.close('all')
        
        # Thread-safe execution redirection inside this child process boundary
        with contextlib.redirect_stdout(stdout_capture):
            exec(code, exec_globals)
            
        # Extract and validate mutated dataset post-execution
        updated_df = exec_globals.get("df")
        if not isinstance(updated_df, pd.DataFrame):
            updated_df = df
            
        # Thread-safely capture any figures generated during runtime
        captured_charts = []
        fig_nums = plt.get_fignums()
        if fig_nums:
            for num in fig_nums:
                fig = plt.figure(num)
                buf = io.BytesIO()
                fig.savefig(buf, format="png", bbox_inches="tight", dpi=180)
                buf.seek(0)
                captured_charts.append(buf.getvalue())
            plt.close('all')
            
        # Stream structured findings back to parent orchestration thread
        response_queue.put({
            "success": True,
            "stdout": stdout_capture.getvalue(),
            "df": updated_df,
            "charts": captured_charts,
            "error_msg": None
        })
        
    except Exception as run_err:
        response_queue.put({
            "success": False,
            "stdout": stdout_capture.getvalue(),
            "df": df,
            "charts": [],
            "error_msg": f"Runtime Exception: {str(run_err)}"
        })

def clean_ai_code(raw: str) -> str:
    code_match = re.search(r"```python\s*(.*?)\s*
```", raw, re.DOTALL | re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip()
    code_match_generic = re.search(r"```\s*(.*?)\s*```", raw, re.DOTALL)
    if code_match_generic:
        return code_match_generic.group(1).strip()
    return raw.strip()

def is_likely_python(code: str) -> bool:
    return any(kw in code for kw in PYTHON_KEYWORDS)

def sanitize_col_name(name: str) -> str:
    return re.sub(r"[^\w\s\-\.]", "_", str(name))

def get_df_summary(df: pd.DataFrame) -> str:
    lines = []
    for col in df.columns:
        safe_col = sanitize_col_name(col)
        dtype    = str(df[col].dtype)
        nulls    = int(df[col].isnull().sum())
        if pd.api.types.is_numeric_dtype(df[col]):
            desc  = df[col].describe()
            stats = f"min={desc['min']:.2f}, max={desc['max']:.2f}, mean={desc['mean']:.2f}"
        else:
            top5  = df[col].dropna().astype(str).value_counts().head(5).index.tolist()
            stats = "top values: " + ", ".join(top5)
        lines.append(f"- `{safe_col}` ({dtype}, {nulls} nulls) → {stats}")
    return "\n".join(lines)

def render_metrics(df: pd.DataFrame):
    num_cols    = df.select_dtypes(include='number').shape[1]
    missing_pct = round(df.isnull().mean().mean() * 100, 1) if not df.empty else 0.0
    mem_kb      = round(df.memory_usage(deep=True).sum() / 1024, 1)
    mem_unit    = "KB" if mem_kb < 1024 else "MB"
    mem_val     = mem_kb if mem_kb < 1024 else round(mem_kb / 1024, 2)
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="label">Rows</div>
            <div class="value">{df.shape[0]:,}</div>
            <div class="sub">records</div>
        </div>
        <div class="metric-card">
            <div class="label">Columns</div>
            <div class="value">{df.shape[1]}</div>
            <div class="sub">{num_cols} numeric</div>
        </div>
        <div class="metric-card">
            <div class="label">Missing</div>
            <div class="value">{missing_pct}<span class="unit">%</span></div>
            <div class="sub">null values</div>
        </div>
        <div class="metric-card">
            <div class="label">Memory</div>
            <div class="value">{mem_val}<span class="unit">{mem_unit}</span></div>
            <div class="sub">in use</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def load_file(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name
    if name.endswith('.csv'):
        raw = uploaded_file.read()
        for enc in ('utf-8', 'latin-1', 'cp1252'):
            try:
                df = pd.read_csv(io.BytesIO(raw), encoding=enc, parse_dates=True)
                break
            except Exception:
                continue
        else:
            raise ValueError("Could not decode CSV.")
    else:
        df = pd.read_excel(uploaded_file, parse_dates=True)
        if df.columns.duplicated().any() or df.columns.isnull().any():
            st.warning(
                "Merged or unnamed header cells detected. "
                "Consider un-merging header rows in Excel before uploading.",
                icon="⚠️",
            )
    for col in df.select_dtypes(include='object').columns:
        try:
            converted = pd.to_datetime(df[col], errors='coerce')
            if converted.notna().sum() / max(len(df), 1) > 0.7:
                df[col] = converted
        except Exception:
            pass
    return df

def call_ai_with_timeout(client, prompt: str, timeout: int = AI_TIMEOUT_SECONDS, max_retries: int = 3) -> str:
    """
    Executes AI requests inside an isolated thread with a hard timeout wall
    and a robust exponential backoff retry system for maximum network resilience.
    """
    def _call():
        return client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        ).text

    last_exception = None
    for attempt in range(max_retries):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(_call)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                last_exception = TimeoutError(f"Nexus AI timed out after {timeout}s.")
            except Exception as e:
                last_exception = e
            
            if attempt < max_retries - 1:
                time.sleep(1.5 * (attempt + 1))
                
    raise last_exception

def trim_memory():
    if len(st.session_state.command_history) > 50:
        st.session_state.command_history = st.session_state.command_history[-50:]
    if len(st.session_state.chart_gallery) > 10:
        st.session_state.chart_gallery = st.session_state.chart_gallery[-10:]
    if len(st.session_state.chat_history) > 20:
        st.session_state.chat_history = st.session_state.chat_history[-20:]

def classify_query(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ['chart','plot','graph','visuali','bar','line','scatter','histogram']):
        return "chart"
    if any(w in q for w in ['filter','where','remove','drop','clean','deduplic']):
        return "transform"
    if any(w in q for w in ['predict','forecast','trend','regression','correlat']):
        return "model"
    if any(w in q for w in ['summar','describ','overview','what is','tell me']):
        return "summary"
    return "analysis"

def parse_ai_response(raw: str) -> dict:
    sections = {"Analysis": "", "Methodology": "", "Code": "", "Insight": ""}
    patterns = {
        "Analysis":    r"##\s*Analysis\s*(.*?)(?=##|\Z)",
        "Methodology": r"##\s*Methodology\s*(.*?)(?=##|\Z)",
        "Code":        r"```python\s*(.*?)\s*
```",
        "Insight":     r"##\s*Insight\s*(.*?)(?=##|\Z)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, raw, re.DOTALL | re.IGNORECASE)
        if m:
            sections[key] = m.group(1).strip()
    return sections

# ============================================================
# SIDEBAR
# ============================================================
plan_label = PLAN_LABELS.get(plan, plan)
trial_days = days_remaining(user) if "trial" in plan else None

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="logo">◈ NEXUS</div>
        <div class="tagline">Excel AI · Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    if is_admin:
        st.markdown("""
        <div style="background:rgba(248, 81, 73, 0.1); border:1px solid rgba(248, 81, 73, 0.3); border-radius:8px;
                    padding:0.6rem 1rem; text-align:center; margin-bottom:1rem;">
            <span style="font-size:0.75rem; color:var(--danger); text-transform:uppercase; letter-spacing:1px; font-weight:700;">
                👑 Master Key Active
            </span>
        </div>
        """, unsafe_allow_html=True)

    plan_color = {"trial": "var(--warning)", "free_trial": "var(--warning)", "basic": "var(--nexus-text-muted)", "premium": "#0099ff", "pro": "var(--nexus-accent)"}.get(plan, "var(--nexus-text-muted)")
    trial_info = f" · {trial_days}d left" if trial_days is not None else ""
    st.markdown(f"""
    <div style="background:var(--nexus-bg-card); border:1px solid var(--nexus-border); border-radius:8px;
                padding:0.6rem 1rem; text-align:center; margin-bottom:1rem;">
        <span style="font-size:0.72rem; color:var(--nexus-text-muted); text-transform:uppercase; letter-spacing:1px;">Active Plan</span><br>
        <span style="font-family:'Space Mono',monospace; color:{plan_color}; font-weight:700;">{plan_label}{trial_info}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">API Configuration</div>', unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIza…")

    st.markdown('<div class="section-label">Session Controls</div>', unsafe_allow_html=True)
    if st.button("🗑️ Reset Session", use_container_width=True):
        for key in ["updated_df", "chart_gallery", "query_text",
                    "command_history", "chat_history", "df", "last_filename",
                    "show_all_data", "show_all_cols", "request_count"]:
            st.session_state[key] = (
                []    if key in ("command_history", "chart_gallery", "chat_history") else
                ""    if key == "query_text" else
                0     if key == "request_count" else
                False if key in ("show_all_data", "show_all_cols") else
                None
            )
        st.rerun()

    if st.session_state.command_history:
        st.markdown('<div class="section-label">Audit Trail</div>', unsafe_allow_html=True)
        with st.expander(f"📝 {len(st.session_state.command_history)} command(s)", expanded=False):
            for entry in reversed(st.session_state.command_history):
                badge   = '<span class="audit-badge-ok">✓ OK</span>'   if entry["ok"] \
                     else '<span class="audit-badge-err">✗ Fail</span>'
                rows_info = ""
                if entry.get("rows_before") is not None:
                    rows_info = f'· {entry["rows_before"]:,} → {entry["rows_after"]:,} rows'
                st.markdown(f"""
                <div class="audit-item">
                    <div class="audit-cmd">{entry["cmd"]}</div>
                    <div class="audit-meta">{badge}<span class="col-pill" style="margin: 0; padding: 0.05rem 0.4rem; font-size: 0.65rem;">{entry["ts"]}</span><span>{rows_info}</span></div>
                </div>
                """, unsafe_allow_html=True)

    remaining = MAX_REQUESTS_PER_SESSION - st.session_state.request_count
    limit_text = "◈ Unlimited requests" if is_admin else f"◈ {remaining}/{MAX_REQUESTS_PER_SESSION} requests left"
    st.markdown(f'<div class="rate-limit-badge">{limit_text}</div>', unsafe_allow_html=True)
    
    if is_admin:
        st.divider()
        if st.button("← Back to Portal", use_container_width=True):
            st.switch_page("pages/4_Admin_Portal.py")
            
    st.divider()
    st.markdown("""
    <div style="background:var(--nexus-bg-card); border:1px solid var(--nexus-border); border-radius:8px;
                padding:0.7rem 1rem; text-align:center;">
        <div style="font-size:0.72rem; color:var(--nexus-text-muted); text-transform:uppercase; letter-spacing:1px;">
            Nexus v4.0 · Pro
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# HERO
# ============================================================
st.markdown("""
<div class="hero-zone fade-up">
    <div class="hero-title">◈ NEXUS Excel AI</div>
    <div class="hero-sub">Professional Spreadsheet Intelligence Engine</div>
</div>
""", unsafe_allow_html=True)

if not api_key:
    st.markdown("""
    <div style="background:var(--nexus-bg-card); border:1px solid var(--nexus-border); border-radius:12px;
                padding:2rem; text-align:center; margin-top:2rem;">
        <div style="font-size:2.5rem; margin-bottom:0.5rem;">🔑</div>
        <div style="font-family:'Space Mono',monospace; color:var(--nexus-text-primary); font-size:1rem;">API Key Required</div>
        <div style="color:var(--nexus-text-muted); font-size:0.875rem; margin-top:0.4rem;">
            Enter your API Key in the sidebar to activate the Nexus engine.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ============================================================
# MAIN CONTENT
# ============================================================
try:
    from google import genai
    client = genai.Client(api_key=api_key)

    st.markdown('<div class="section-label">Data Source</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload spreadsheet",
        type=["xlsx", "csv"],
        label_visibility="collapsed",
        help="Supported: .csv and .xlsx · Max 10 MB",
    )

    if uploaded_file is not None:
        if st.session_state.last_filename != uploaded_file.name:
            with st.spinner("Processing file..."):
                try:
                    df = load_file(uploaded_file)
                    st.session_state.df = df
                    st.session_state.updated_df = df.copy()
                    st.session_state.last_filename = uploaded_file.name
                    st.session_state.chart_gallery = []
                    st.session_state.chat_history = []
                    st.success("File uploaded successfully!")
                except Exception as e:
                    st.error(f"Error reading file: {e}")

        if st.session_state.df is not None:
            active_df = st.session_state.updated_df if st.session_state.updated_df is not None else st.session_state.df
            
            render_metrics(active_df)

            st.markdown('<div class="section-label">Dataset Columns</div>', unsafe_allow_html=True)
            col_list = active_df.columns.tolist()
            
            col_expanded = st.checkbox("Show all columns as pills", value=st.session_state.show_all_cols)
            st.session_state.show_all_cols = col_expanded
            
            pills_class = "col-pills-wrap expanded" if col_expanded else "col-pills-wrap"
            pills_html = f'<div class="{pills_class}">'
            for c in col_list:
                pills_html += f'<span class="col-pill">{sanitize_col_name(c)} ({str(active_df[c].dtype)})</span>'
            pills_html += '</div>'
            st.markdown(pills_html, unsafe_allow_html=True)

            st.markdown('<div class="section-label">Dataset Preview</div>', unsafe_allow_html=True)
            
            show_all_rows = st.checkbox("Show all records", value=st.session_state.show_all_data)
            st.session_state.show_all_data = show_all_rows
            
            preview_rows = active_df if show_all_rows else active_df.head(15)
            st.dataframe(preview_rows, use_container_width=True)

            st.markdown('<div class="section-label">AI Conversation & Command Centre</div>', unsafe_allow_html=True)
            
            col_prompt, col_mic = st.columns([8, 2])
            with col_prompt:
                _prefill = st.session_state.get("prefill_query", "")
                if "prefill_query" in st.session_state:
                    del st.session_state["prefill_query"]

                user_prompt = st.text_area(
                    "What would you like to analyze?",
                    value=_prefill,
                    placeholder="E.g., 'Draw a bar chart of the sales grouped by category' or 'Filter the rows where age > 30 and save it'",
                    key="query_text_area",
                    height=90
                )
            
            voice_txt = ""
            with col_mic:
                st.markdown('<div style="text-align: center; margin-top: 15px;">', unsafe_allow_html=True)
                if VOICE_COMMAND_SUPPORT:
                    st.write("🎙️ Voice Command")
                    audio_record = mic_recorder(
                        start_prompt="Record Command 🎤",
                        stop_prompt="Stop Recording 🛑",
                        key="voice_mic_recorder"
                    )
                    if audio_record:
                        st.info("🎙️ Voice transcription integration coming soon.")
                else:
                    st.write("Voice Command (Disabled)")
                    st.caption("Install `streamlit-mic-recorder` to enable voice.")
                st.markdown('</div>', unsafe_allow_html=True)

            query_to_run = user_prompt.strip()

            st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
            run_btn = st.button("⚡ Execute AI Analysis", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            if run_btn and query_to_run:
                if not is_admin and st.session_state.request_count >= MAX_REQUESTS_PER_SESSION:
                    st.error("Rate limit reached. Please contact your administrator to upgrade your plan.")
                else:
                    st.session_state.request_count += 1
                    
                    df_summary = get_df_summary(active_df)
                    
                    history_block = ""
                    if st.session_state.chat_history:
                        history_block = "CONVERSATION HISTORY (most recent last):\n"
                        for msg in st.session_state.chat_history[-10:]:
                            role = "User" if msg["role"] == "user" else "Nexus AI"
                            history_block += f"{role}: {msg['content'][:300]}\n"
                    
                    system_prompt = f"""
  You are Nexus AI, an elite data analyst and Python engineer embedded
  inside a professional spreadsheet intelligence platform.

  ── DATASET SCHEMA ──
  {df_summary}

  ── TOTAL ROWS: {len(active_df):,} · COLUMNS: {active_df.shape[1]} ──

  ── CONVERSATION HISTORY ──
  {history_block if history_block else "No prior context."}

  ── CURRENT REQUEST ──
  {query_to_run}

  ── YOUR RESPONSE MUST FOLLOW THIS EXACT STRUCTURE ──

  ## Analysis
  Write 2–5 sentences explaining what you found or what the code does.
  Be precise — include real column names, data types, and numeric
  observations from the schema. Do not be generic.

  ## Methodology
  Briefly describe the analytical approach (e.g. "groupby aggregation",
  "linear interpolation", "outlier detection using IQR").

  ## Code
  If computation is needed, produce ONE clean ```python``` block:
  - Operate on the `df` variable directly.
  - For plots: use matplotlib or seaborn. Apply dark theme first:
      plt.style.use('dark_background')
      fig, ax = plt.subplots(figsize=(10, 5))
    Add a title, axis labels, and gridlines. Do NOT call plt.show().
  - For mutations: assign back to df (e.g. df = df[...]).
  - Never import os, sys, subprocess, shutil, or any stdlib outside
    of pandas, numpy, matplotlib, and seaborn.
  - If no code is needed, omit the block entirely.

  ## Insight
  End with 1–3 bullet points of actionable business insight derived
  from the data. Ground every claim in the actual schema values.
  """
                    
                    spinner_labels = {
                        "chart":     "◈ Rendering visualisation...",
                        "transform": "◈ Applying data transformation...",
                        "model":     "◈ Running predictive model...",
                        "summary":   "◈ Generating data summary...",
                        "analysis":  "◈ Running deep analysis...",
                    }
                    classified_cat = classify_query(query_to_run)
                    
                    with st.spinner(spinner_labels[classified_cat]):
                        try:
                            ai_response = call_ai_with_timeout(client, system_prompt)
                            
                            st.session_state.chat_history.append({"role": "user", "content": query_to_run})
                            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                            
                            parsed = parse_ai_response(ai_response)
                            
                            st.markdown("""
                            <div class="results-panel">
                                <h4 style="font-family:'Space Mono',monospace; color:var(--nexus-accent); margin-top:0;">
                                    ◈ AI REASONING & FINDINGS
                                </h4>
                            """, unsafe_allow_html=True)
                            st.markdown(parsed["Analysis"] if parsed["Analysis"] else ai_response)
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            if parsed["Methodology"]:
                                st.markdown(f"""
                                <div style="background:var(--nexus-bg-card); border:1px solid var(--nexus-border); border-radius:8px;
                                            padding:0.75rem 1rem; margin-top:0.75rem;">
                                    <div style="font-size:0.72rem; color:var(--nexus-text-muted); text-transform:uppercase; letter-spacing:1px; font-family:'Space Mono',monospace; margin-bottom:0.25rem;">
                                        Methodology
                                    </div>
                                    <div style="font-size:0.875rem; color:var(--nexus-text-primary);">{parsed["Methodology"]}</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                            extracted_code = parsed["Code"]
                            if extracted_code and is_likely_python(extracted_code):
                                st.markdown("### 💻 Executed Python Logic")
                                st.code(extracted_code, language="python")
                                
                                # Defense-In-Depth: Hard structural validation pass before dispatching to sandbox
                                blocked_tokens = ['st.secrets', 'os.', 'sys.', 'subprocess', 'shutil', 'open(', 'eval(', 'exec(']
                                found_violations = [tk for tk in blocked_tokens if tk in extracted_code]
                                
                                if found_violations:
                                    st.error(f"❌ Security Blocked: Malicious syntax patterns identified: {', '.join(found_violations)}")
                                    execution_success = False
                                else:
                                    # Initialize communication pipe and process lifecycle structures
                                    communication_queue = multiprocessing.Queue()
                                    sandbox_process = multiprocessing.Process(
                                        target=_secure_sandbox_worker,
                                        args=(extracted_code, active_df.copy(), communication_queue)
                                    )
                                    
                                    execution_success = False
                                    SANDBOX_HARD_TIMEOUT = 12  # Hardware enforcement boundary to crush infinite loops
                                    
                                    try:
                                        sandbox_process.start()
                                        
                                        # Wait for worker process execution completion with a hard limit
                                        sandbox_process.join(timeout=SANDBOX_HARD_TIMEOUT)
                                        
                                        if sandbox_process.is_alive():
                                            # Kill process instantly if it exceeds the runtime threshold
                                            sandbox_process.terminate()
                                            sandbox_process.join()
                                            st.error(f"❌ Execution Blocked: Code surpassed the hardware time threshold of {SANDBOX_HARD_TIMEOUT}s.")
                                        else:
                                            # Pull metrics from the worker queue if execution finishes successfully
                                            if not communication_queue.empty():
                                                run_result = communication_queue.get()
                                                execution_success = run_result["success"]
                                                
                                                # Render safely captured standard output streams
                                                if run_result["stdout"]:
                                                    st.markdown("#### 📝 Print Outputs")
                                                    st.text(run_result["stdout"])
                                                    
                                                if execution_success:
                                                    # Update global session data with mutated states securely
                                                    st.session_state.updated_df = run_result["df"]
                                                    active_df = run_result["df"]
                                                    
                                                    # Append rendered data charts into display memory safely
                                                    for chart_bytes in run_result["charts"]:
                                                        st.session_state.chart_gallery.append(chart_bytes)
                                                        st.image(chart_bytes, use_container_width=True)
                                                else:
                                                    st.error(run_result["error_msg"])
                                            else:
                                                st.error("❌ Sandbox Execution Error: Subprocess died without returning data.")
                                                
                                    except Exception as orchestration_err:
                                        st.error(f"Engine Orchestration Fault: {orchestration_err}")
                                    finally:
                                        # Ensure proper resource cleanup
                                        if sandbox_process.is_alive():
                                            sandbox_process.kill()
                                            sandbox_process.join()
                                            
                                # Log to the localized app audit timeline
                                st.session_state.command_history.append({
                                    "cmd": query_to_run,
                                    "ok": execution_success,
                                    "ts": datetime.datetime.now().strftime("%H:%M:%S"),
                                    "rows_before": len(st.session_state.df),
                                    "rows_after": len(active_df)
                                })
                                trim_memory()
                            else:
                                st.session_state.command_history.append({
                                    "cmd": query_to_run,
                                    "ok": True,
                                    "ts": datetime.datetime.now().strftime("%H:%M:%S"),
                                    "rows_before": len(active_df),
                                    "rows_after": len(active_df)
                                })
                                trim_memory()
                            
                            if parsed["Insight"]:
                                st.markdown(f"""
                                <div style="border-left:3px solid var(--nexus-accent); background:var(--nexus-bg-card); border-radius:4px;
                                            padding:0.75rem 1rem; margin-top:0.75rem;">
                                    <div style="font-size:0.72rem; color:var(--nexus-text-muted); text-transform:uppercase; letter-spacing:1px; font-family:'Space Mono',monospace; margin-bottom:0.25rem;">
                                        Actionable Insights
                                    </div>
                                    <div style="font-size:0.875rem; color:var(--nexus-text-primary);">{parsed["Insight"]}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.success("Analysis executed successfully!")
                            
                            followup_prompt = f"""
                            The user asked: "{query_to_run}"
                            Dataset columns: {', '.join(active_df.columns[:15].tolist())}
                            Suggest exactly 3 short follow-up analysis questions (max 12 words
                            each) the user might ask next. Return ONLY a JSON array of 3 strings.
                            Example: ["What is the average by category?", "Show top 10 rows by revenue.", "Plot monthly trend."]
                            """
                            
                            suggestions = []
                            try:
                                res_suggestions = call_ai_with_timeout(client, followup_prompt, timeout=10)
                                json_match = re.search(r"\[\s*.*?\s*\]", res_suggestions, re.DOTALL)
                                if json_match:
                                    suggestions = json.loads(json_match.group(0))
                                else:
                                    suggestions = json.loads(res_suggestions.strip())
                            except Exception:
                                pass
                            
                            if suggestions and len(suggestions) >= 3:
                                st.markdown("<br><strong>◈ Suggested next questions:</strong>", unsafe_allow_html=True)
                                cols_sug = st.columns(3)
                                for i, q in enumerate(suggestions[:3]):
                                    if cols_sug[i].button(q, key=f"sug_{st.session_state.request_count}_{i}", use_container_width=True):
                                        st.session_state["prefill_query"] = q
                                        st.rerun()
                            
                        except Exception as e:
                            st.error(f"Analysis engine failed: {e}")
                            
            if st.session_state.chart_gallery:
                st.markdown('<div class="section-label">Recent Chart Gallery</div>', unsafe_allow_html=True)
                cols_charts = st.columns(2)
                for idx, chart_bytes in enumerate(st.session_state.chart_gallery):
                    col_target = cols_charts[idx % 2]
                    with col_target:
                        st.markdown(f'<div class="chart-gallery-item"><div class="chart-gallery-label">Plot {idx+1}</div></div>', unsafe_allow_html=True)
                        st.image(chart_bytes, use_container_width=True)
                        
            st.markdown('<div class="section-label">Export Data</div>', unsafe_allow_html=True)
            col_csv, col_xlsx = st.columns(2)
            with col_csv:
                csv_data = active_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV File",
                    data=csv_data,
                    file_name="nexus_analyst_export.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_xlsx:
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    active_df.to_excel(writer, index=False, sheet_name="Nexus AI Export")
                excel_data = excel_buffer.getvalue()
                st.download_button(
                    label="📥 Download Excel File",
                    data=excel_data,
                    file_name="nexus_analyst_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

    else:
        st.markdown("""
        <div style="background:var(--nexus-bg-card); border:2px dashed var(--nexus-border); border-radius:12px;
                    padding:4rem 1rem; text-align:center;">
            <div style="font-size:3rem; margin-bottom:1rem;">📂</div>
            <div style="font-family:'Space Mono',monospace; color:var(--nexus-text-primary); font-size:1.15rem; font-weight:700;">
                Ready for Analysis
            </div>
            <p style="color:var(--nexus-text-muted); font-size:0.875rem; max-width:400px; margin:0.5rem auto 0 auto;">
                Spreadsheet uploaded. AI is standing by to write formulas, filters, and graphs.
            </p>
        </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error initializing dashboard components: {e}")
