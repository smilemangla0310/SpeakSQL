"""
SpeakSQL — Main Streamlit Application
Natural Language to SQL Copilot with premium dark dashboard UI.
"""

import streamlit as st
import pandas as pd
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import (
    APP_TITLE, APP_ICON, APP_SUBTITLE, APP_VERSION,
    PAGE_CONFIG, SAMPLE_QUERIES, THEME,
    LLM_PROVIDERS, DEFAULT_PROVIDER, TEMPERATURE, MAX_RETRIES,
    GROQ_API_KEY, HF_API_KEY, GOOGLE_API_KEY,
    DEMO_DB_PATH, DEFAULT_ROW_LIMIT,
)
from app.ui_components import (
    inject_theme, render_header, render_footer,
    render_status_badge, render_section_header,
    render_sql_panel, render_results_table, render_explanation_card,
    render_schema_browser, render_empty_state,
    render_error_banner, render_safety_warning,
    render_metric_card, render_sidebar_divider,
    render_loading_dots,
)
from db.connection import DatabaseManager
from db.schema_inspector import inspect_schema, format_schema_for_llm, get_schema_summary
from db.seed_demo import seed_demo_database
from viz.chart_engine import render_all_suggested_charts

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(**PAGE_CONFIG)
inject_theme()


# ── Session State ─────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "db_manager": None,
        "schema": None,
        "schema_str": "",
        "schema_summary": None,
        "agent": None,
        "query_history": [],
        "current_sql": "",
        "current_result": None,
        "processing": False,
        "provider_name": DEFAULT_PROVIDER,
        "api_key": "",
        "model_name": "",
        "agent_config_hash": "",
        "db_initialized": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# Safety: reset stale provider
if st.session_state.provider_name not in LLM_PROVIDERS:
    st.session_state.provider_name = DEFAULT_PROVIDER


def _env_key(provider_name: str) -> str:
    p = LLM_PROVIDERS[provider_name]
    if p["key"] == "groq": return GROQ_API_KEY
    if p["key"] == "huggingface": return HF_API_KEY
    if p["key"] == "gemini": return GOOGLE_API_KEY
    return ""


def _config_hash(pn, ak, mn):
    return f"{pn}|{ak[:8] if ak else ''}|{mn}"


def ensure_demo_db():
    """Ensure the demo database exists and is connected."""
    if st.session_state.db_initialized and st.session_state.db_manager:
        return

    # Seed demo DB if it doesn't exist
    if not os.path.exists(DEMO_DB_PATH):
        with st.spinner("🔧 Creating demo database..."):
            seed_demo_database(DEMO_DB_PATH)

    # Connect
    try:
        dm = DatabaseManager(db_path=DEMO_DB_PATH)
        ok, msg = dm.test_connection()
        if ok:
            st.session_state.db_manager = dm
            schema = inspect_schema(dm.engine)
            st.session_state.schema = schema
            st.session_state.schema_str = format_schema_for_llm(schema)
            st.session_state.schema_summary = get_schema_summary(schema)
            st.session_state.db_initialized = True
    except Exception as e:
        st.error(f"Database connection failed: {e}")


def get_agent(provider_name, api_key, model_name):
    """Get or create the SQL agent."""
    h = _config_hash(provider_name, api_key, model_name)
    if st.session_state.agent is None or st.session_state.agent_config_hash != h:
        if not api_key:
            return None
        try:
            from agent.sql_agent import SQLAgent
            pk = LLM_PROVIDERS[provider_name]["key"]
            st.session_state.agent = SQLAgent(
                db_manager=st.session_state.db_manager,
                schema_str=st.session_state.schema_str,
                provider_key=pk, api_key=api_key, model_name=model_name,
                temperature=TEMPERATURE, max_retries=MAX_RETRIES,
                row_limit=DEFAULT_ROW_LIMIT,
            )
            st.session_state.agent_config_hash = h
        except Exception as e:
            st.error(f"Agent init failed: {e}")
            return None
    return st.session_state.agent


# Initialize demo DB
ensure_demo_db()


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 12px; padding: 8px 0 4px 0;">
        <div style="
            width: 38px; height: 38px;
            background: {THEME['accent_gradient']};
            border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
            font-size: 20px;
            box-shadow: {THEME['glow_primary']};
        ">🗣️</div>
        <div>
            <p style="margin:0; font-size: 1.05rem; font-weight: 700; color: {THEME['text_primary']};">SpeakSQL</p>
            <p style="margin:0; font-size: 0.68rem; color: {THEME['text_muted']};">NL→SQL Copilot · v{APP_VERSION}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    render_sidebar_divider()

    # ── Database Info ─────────────────────────────────────────────────
    st.markdown(f"<p style='color:{THEME['text_muted']};font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;'>🗄️ Database</p>", unsafe_allow_html=True)

    if st.session_state.db_initialized and st.session_state.schema_summary:
        s = st.session_state.schema_summary
        st.markdown(f"""
        <div style="
            background: {THEME['bg_elevated']};
            border: 1px solid {THEME['border']};
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 8px;
        ">
            <div style="margin-bottom: 6px;">
                <span style="color: {THEME['text_primary']}; font-weight: 600; font-size: 0.82rem;">📁 Demo HR + Sales DB</span>
                {render_status_badge("Connected", "success")}
            </div>
            <div style="color: {THEME['text_muted']}; font-size: 0.72rem;">
                📋 {s['tables']} tables &nbsp;&nbsp; 📊 {s['columns']} columns &nbsp;&nbsp; 📐 {s['rows']:,} rows
            </div>
        </div>
        """, unsafe_allow_html=True)

    render_sidebar_divider()

    # ── Schema Browser ────────────────────────────────────────────────
    st.markdown(f"<p style='color:{THEME['text_muted']};font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;'>🔍 Schema Browser</p>", unsafe_allow_html=True)

    if st.session_state.schema:
        render_schema_browser(st.session_state.schema)

    render_sidebar_divider()

    # ── Model Selection ───────────────────────────────────────────────
    provider_name = DEFAULT_PROVIDER
    st.session_state.provider_name = provider_name
    pcfg = LLM_PROVIDERS[provider_name]

    st.markdown(f"<p style='color:{THEME['text_muted']};font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;'>🤖 AI Model</p>", unsafe_allow_html=True)
    model_name = st.selectbox("Model", options=pcfg["models"], index=0, label_visibility="collapsed")

    api_key = _env_key(provider_name)
    st.session_state.api_key = api_key

    render_sidebar_divider()

    # ── Query History ─────────────────────────────────────────────────
    if st.session_state.query_history:
        st.markdown(f"<p style='color:{THEME['text_muted']};font-size:0.72rem;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;'>🕘 Query History</p>", unsafe_allow_html=True)
        for i, item in enumerate(reversed(st.session_state.query_history[-8:])):
            status = "success" if not item.get("error") else "error"
            badge = "🟢" if status == "success" else "🔴"
            q = item["question"]
            if st.button(f"{badge} {q[:45]}{'…' if len(q)>45 else ''}", key=f"hist_{i}", use_container_width=True):
                st.session_state.current_sql = item.get("sql", "")
                st.rerun()

    render_sidebar_divider()

    # Controls
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.query_history = []
            st.session_state.current_sql = ""
            st.session_state.current_result = None
            if st.session_state.agent:
                st.session_state.agent.clear_memory()
            st.rerun()
    with c2:
        if st.button("🔄 Reset", use_container_width=True):
            for k in ["query_history", "current_sql", "current_result", "agent", "agent_config_hash"]:
                st.session_state[k] = [] if k == "query_history" else "" if isinstance(st.session_state.get(k), str) else None
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

render_header()

has_key = bool(st.session_state.api_key)
has_db = st.session_state.db_initialized

# ── Status Bar ────────────────────────────────────────────────────────────────
status_cols = st.columns([2, 2, 2, 2, 4])
with status_cols[0]:
    if has_key:
        st.markdown(render_status_badge("● API Connected", "success"), unsafe_allow_html=True)
    else:
        st.markdown(render_status_badge("○ API Key Missing", "warning"), unsafe_allow_html=True)
with status_cols[1]:
    if has_db:
        st.markdown(render_status_badge("● DB Connected", "success"), unsafe_allow_html=True)
    else:
        st.markdown(render_status_badge("○ No Database", "warning"), unsafe_allow_html=True)
with status_cols[2]:
    if st.session_state.schema_summary:
        s = st.session_state.schema_summary
        st.markdown(render_status_badge(f"📋 {s['tables']} tables", "info"), unsafe_allow_html=True)
with status_cols[3]:
    st.markdown(render_status_badge(f"🤖 {provider_name.split('(')[0].strip()}", "info"), unsafe_allow_html=True)

st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)


# ── Main Input Area ──────────────────────────────────────────────────────────
if not has_key:
    st.warning("⚠️ API key not found. Add your `GROQ_API_KEY` to the `.env` file to get started.")

if not has_db:
    st.error("❌ Database not connected. Check the demo database setup.")

if has_key and has_db:
    # ── Sample Queries (when no history) ─────────────────────────────
    if not st.session_state.query_history:
        render_section_header("Ask Your Database", "Type a question or try a sample below", "💬")
        q_cols = st.columns(2)
        for i, (icon, query) in enumerate(SAMPLE_QUERIES[:6]):
            with q_cols[i % 2]:
                if st.button(f"{icon}  {query}", key=f"sq_{i}", use_container_width=True):
                    st.session_state._pending_query = query
                    st.rerun()

    # ── NL Input ─────────────────────────────────────────────────────
    st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

    input_cols = st.columns([6, 1])
    with input_cols[0]:
        user_question = st.text_input(
            "Ask a question",
            placeholder="e.g., List employees in each department with their average salary…",
            label_visibility="collapsed",
            key="nl_input",
        )
    with input_cols[1]:
        generate_clicked = st.button("🧠 Generate", type="primary", use_container_width=True)

    # Check for pending query from sample buttons
    pending = st.session_state.pop("_pending_query", None)
    if pending:
        user_question = pending
        generate_clicked = True

    # ── Generate SQL Pipeline ────────────────────────────────────────
    if generate_clicked and user_question:
        agent = get_agent(provider_name, api_key, model_name)
        if not agent:
            render_error_banner(f"Agent initialization failed. {pcfg['help']}")
        else:
            status_ctr = st.empty()
            status_msgs = []

            def _status_cb(msg):
                status_msgs.append(msg)
                status_ctr.markdown(
                    f"<div style='color:{THEME['text_muted']};font-size:0.8rem;padding:8px 0;'>"
                    + " → ".join(status_msgs[-3:]) + "</div>",
                    unsafe_allow_html=True,
                )

            st.session_state.processing = True
            try:
                resp = agent.full_pipeline(user_question, status_callback=_status_cb)
            finally:
                st.session_state.processing = False

            status_ctr.empty()

            # Store result
            st.session_state.current_result = resp
            st.session_state.current_sql = resp.sql

            # Add to history
            st.session_state.query_history.append({
                "question": user_question,
                "sql": resp.sql,
                "error": resp.error,
                "time": resp.execution_time,
            })

            st.rerun()

    # ── Display Current Result ───────────────────────────────────────
    resp = st.session_state.current_result

    if resp:
        # Safety warning
        if resp.safety_warning:
            render_safety_warning(resp.safety_warning)

        # Error
        elif resp.error and not resp.df is not None:
            render_error_banner(resp.error)

        # SQL Panel + Results
        if resp.sql:
            st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

            # SQL Panel
            render_sql_panel(resp.sql)

            # Editable SQL + Run button
            edit_cols = st.columns([5, 1, 1])
            with edit_cols[0]:
                edited_sql = st.text_area(
                    "Edit SQL",
                    value=resp.sql,
                    height=120,
                    label_visibility="collapsed",
                    key="sql_editor",
                )
            with edit_cols[1]:
                copy_clicked = st.button("📋 Copy", use_container_width=True)
            with edit_cols[2]:
                run_clicked = st.button("▶️ Run", type="primary", use_container_width=True)

            if copy_clicked:
                st.toast("📋 SQL copied to clipboard!", icon="✅")

            # Run edited SQL
            if run_clicked and edited_sql:
                agent = get_agent(provider_name, api_key, model_name)
                if agent:
                    custom_resp = agent.run_custom_sql(edited_sql)
                    if custom_resp.error:
                        render_error_banner(custom_resp.error)
                    else:
                        resp = custom_resp
                        resp.sql = edited_sql
                        st.session_state.current_result = resp

            # Results Tabs
            if resp.df is not None and not resp.df.empty:
                st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

                # Execution info bar
                info_parts = []
                if resp.execution_time:
                    info_parts.append(f"⚡ {resp.execution_time}s")
                if resp.row_count:
                    info_parts.append(f"📐 {resp.row_count} rows")
                if resp.truncated:
                    info_parts.append(f"⚠️ Truncated to {DEFAULT_ROW_LIMIT} rows")

                if info_parts:
                    st.markdown(f"""
                    <div style="
                        display: flex; gap: 16px;
                        color: {THEME['text_muted']};
                        font-size: 0.78rem;
                        padding: 4px 0 8px 0;
                    ">{"&nbsp;&nbsp;·&nbsp;&nbsp;".join(info_parts)}</div>
                    """, unsafe_allow_html=True)

                tab_results, tab_charts, tab_explain = st.tabs(["📊 Results", "📈 Charts", "💡 Explanation"])

                with tab_results:
                    render_results_table(resp.df, resp.quick_stats)

                with tab_charts:
                    charts = render_all_suggested_charts(resp.df)
                    if charts:
                        for chart_type, fig in charts:
                            st.plotly_chart(fig, use_container_width=True, key=f"chart_{chart_type}_{id(fig)}")
                    else:
                        render_empty_state(
                            "No Charts Available",
                            "The result set doesn't have the right column types for auto-charting. Try a query with numeric and categorical columns.",
                            "📈"
                        )

                with tab_explain:
                    if resp.explanation:
                        render_explanation_card(resp.explanation)
                    else:
                        render_empty_state(
                            "No Explanation",
                            "Explanation will appear here after a successful query.",
                            "💡"
                        )

            elif resp.error and resp.sql:
                render_error_banner(resp.error)

    elif not st.session_state.query_history:
        # First-time empty state
        render_empty_state(
            "Ask Your First Question",
            "Type a question in natural English above, or click a sample query to get started. SpeakSQL will generate safe SQL, execute it, and show you results with charts.",
            "🗣️"
        )


# ── Footer ────────────────────────────────────────────────────────────────────
render_footer()
