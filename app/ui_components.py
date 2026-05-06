"""
SpeakSQL — Premium dark-theme UI components.
SQL panels, schema browser, results tables, chart containers, query history.
"""

import streamlit as st
import pandas as pd
from app.config import THEME


# ── CSS Theme Injection ───────────────────────────────────────────────────────

PREMIUM_CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}
    .stApp {{
        background: {THEME['bg_primary']} !important;
    }}

    #MainMenu, footer {{visibility: hidden;}}
    header {{background: transparent !important;}}
    .stDeployButton {{display: none;}}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: {THEME['bg_surface']} !important;
        border-right: 1px solid {THEME['border']} !important;
    }}
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {{
        color: {THEME['text_secondary']} !important;
        font-size: 0.85rem;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background: {THEME['bg_surface']};
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
        border: 1px solid {THEME['border']};
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 8px;
        color: {THEME['text_muted']};
        font-weight: 500;
        font-size: 0.9rem;
        padding: 8px 20px;
        background: transparent;
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background: {THEME['accent_primary']} !important;
        color: white !important;
        font-weight: 600;
    }}
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {{
        display: none;
    }}

    /* Expanders */
    .streamlit-expanderHeader {{
        background: {THEME['bg_surface']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 10px !important;
        color: {THEME['text_primary']} !important;
        font-weight: 600 !important;
    }}
    .streamlit-expanderContent {{
        background: {THEME['bg_surface']} !important;
        border: 1px solid {THEME['border']} !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
    }}

    /* Buttons */
    .stButton > button {{
        background: {THEME['bg_elevated']} !important;
        color: {THEME['text_primary']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
        padding: 6px 16px !important;
    }}
    .stButton > button:hover {{
        border-color: {THEME['accent_primary']} !important;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2) !important;
        transform: translateY(-1px) !important;
    }}
    .stButton > button[kind="primary"] {{
        background: {THEME['accent_primary']} !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        box-shadow: 0 6px 16px rgba(245, 158, 11, 0.3) !important;
        transform: translateY(-2px) !important;
    }}

    /* Text Input */
    .stTextInput > div > div {{
        background: {THEME['bg_elevated']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 8px !important;
        color: {THEME['text_primary']} !important;
    }}
    .stTextInput > div > div:focus-within {{
        border-color: {THEME['accent_primary']} !important;
        box-shadow: {THEME['glow_primary']} !important;
    }}

    /* Text Area */
    .stTextArea > div > div > textarea {{
        background: {THEME['bg_elevated']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 8px !important;
        color: {THEME['text_primary']} !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
    }}

    /* Select Box */
    .stSelectbox > div > div {{
        background: {THEME['bg_elevated']} !important;
        border: 1px solid {THEME['border']} !important;
        border-radius: 8px !important;
        color: {THEME['text_primary']} !important;
    }}

    /* DataFrame */
    .stDataFrame {{
        border: 1px solid {THEME['border']} !important;
        border-radius: 10px !important;
        overflow: hidden;
    }}

    /* Code Block */
    .stCodeBlock {{
        border: 1px solid {THEME['border']} !important;
        border-radius: 10px !important;
    }}

    /* Alerts */
    .stAlert {{
        border-radius: 10px !important;
        border: 1px solid {THEME['border']} !important;
    }}

    /* Scrollbar */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: {THEME['bg_primary']}; }}
    ::-webkit-scrollbar-thumb {{ background: {THEME['border_accent']}; border-radius: 3px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: {THEME['text_muted']}; }}

    hr {{ border-color: {THEME['border']} !important; opacity: 0.5; }}
</style>
"""


def inject_theme():
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)


def render_header():
    st.markdown(f"""
    <div style="
        background: {THEME['bg_surface']};
        border: 1px solid {THEME['border']};
        border-radius: 16px;
        padding: 20px 32px;
        margin-bottom: 24px;
        display: flex; align-items: center; justify-content: space-between;
    ">
        <div style="display: flex; align-items: center; gap: 16px;">
            <div style="
                width: 48px; height: 48px;
                background: {THEME['accent_gradient']};
                border-radius: 14px;
                display: flex; align-items: center; justify-content: center;
                font-size: 24px;
                box-shadow: {THEME['glow_primary']};
            ">🗣️</div>
            <div>
                <h1 style="
                    margin: 0; padding: 0;
                    font-size: 1.7rem; font-weight: 800;
                    color: {THEME['text_primary']};
                    letter-spacing: -0.5px;
                ">SpeakSQL</h1>
                <p style="
                    margin: 0; padding: 0;
                    font-size: 0.82rem;
                    color: {THEME['text_muted']};
                    font-weight: 400;
                ">Natural Language to SQL Copilot</p>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="
                background: {THEME['bg_elevated']};
                border: 1px solid {THEME['border']};
                border-radius: 20px;
                padding: 4px 14px;
                font-size: 0.75rem;
                color: {THEME['text_muted']};
                font-weight: 500;
            ">v1.0</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_status_badge(text: str, status: str = "info") -> str:
    colors = {
        "success": (THEME['success'], "rgba(16, 185, 129, 0.1)"),
        "warning": (THEME['warning'], "rgba(245, 158, 11, 0.1)"),
        "error": (THEME['error'], "rgba(239, 68, 68, 0.1)"),
        "info": (THEME['accent_primary'], "rgba(6, 182, 212, 0.1)"),
        "active": (THEME['accent_secondary'], "rgba(139, 92, 246, 0.1)"),
    }
    fg, bg = colors.get(status, colors["info"])
    return f"""<span style="
        background: {bg}; color: {fg};
        border: 1px solid {fg}33;
        border-radius: 6px; padding: 2px 10px;
        font-size: 0.72rem; font-weight: 600; letter-spacing: 0.3px;
    ">{text}</span>"""


def render_section_header(title: str, subtitle: str = "", icon: str = ""):
    st.markdown(f"""
    <div style="margin: 24px 0 16px 0;">
        <h3 style="
            margin: 0; padding: 0;
            color: {THEME['text_primary']};
            font-size: 1.1rem; font-weight: 700;
            display: flex; align-items: center; gap: 8px;
        ">{icon} {title}</h3>
        {"<p style='margin: 4px 0 0 0; color: " + THEME['text_muted'] + "; font-size: 0.8rem;'>" + subtitle + "</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def render_sql_panel(sql: str):
    """Display generated SQL with syntax highlighting."""
    st.markdown(f"""
    <div style="
        background: {THEME['bg_surface']};
        border: 1px solid {THEME['border']};
        border-left: 3px solid {THEME['accent_primary']};
        border-radius: 12px;
        padding: 16px 20px;
        margin: 8px 0;
    ">
        <div style="
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 10px; padding-bottom: 8px;
            border-bottom: 1px solid {THEME['border']};
        ">
            <span style="color: {THEME['text_muted']}; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                📝 Generated SQL
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.code(sql, language="sql", line_numbers=True)


def render_results_table(df: pd.DataFrame, stats: dict):
    """Display results with quick stats bar."""
    if df is None or df.empty:
        render_empty_state("No results", "The query returned no rows.", "📭")
        return

    # Stats bar
    stat_items = [f"📐 **{stats.get('row_count', len(df))}** rows"]
    stat_items.append(f"📊 **{stats.get('column_count', len(df.columns))}** columns")

    if stats.get("numeric_stats"):
        for col, s in list(stats["numeric_stats"].items())[:2]:
            if s.get("avg") is not None:
                stat_items.append(f"📈 {col}: avg **{s['avg']:,.2f}**")

    st.markdown(f"""
    <div style="
        background: {THEME['bg_surface']};
        border: 1px solid {THEME['border']};
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 12px;
        display: flex; gap: 20px; flex-wrap: wrap;
        font-size: 0.82rem;
        color: {THEME['text_secondary']};
    ">
        {"&nbsp;&nbsp;·&nbsp;&nbsp;".join(stat_items)}
    </div>
    """, unsafe_allow_html=True)

    st.dataframe(df, use_container_width=True, height=min(500, 40 + len(df) * 35))


def render_explanation_card(explanation: str):
    """Display AI insight panel."""
    if not explanation:
        return
    st.markdown(f"""
    <div style="
        background: {THEME['bg_surface']};
        border: 1px solid {THEME['border']};
        border-left: 3px solid {THEME['accent_primary']};
        border-radius: 14px;
        padding: 22px;
    ">
        <div style="
            display: flex; align-items: center; gap: 8px;
            margin-bottom: 12px; padding-bottom: 10px;
            border-bottom: 1px solid {THEME['border']};
        ">
            <span style="font-size: 1.1rem;">💡</span>
            <span style="color: {THEME['text_primary']}; font-weight: 600; font-size: 0.95rem;">AI Insight</span>
        </div>
        <div style="color: {THEME['text_secondary']}; font-size: 0.9rem; line-height: 1.7;">
            {explanation}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_schema_browser(schema: dict):
    """Render collapsible schema tree in sidebar."""
    for table_name, info in schema.items():
        with st.expander(f"📋 {table_name} ({info['row_count']} rows)", expanded=False):
            for col in info["columns"]:
                pk = " 🔑" if col["name"] in info.get("primary_key", []) else ""
                nullable = "" if col.get("nullable", True) else " •"
                st.markdown(f"""
                <div style="
                    padding: 3px 0;
                    font-size: 0.78rem;
                    color: {THEME['text_secondary']};
                    border-bottom: 1px solid {THEME['border']}22;
                ">
                    <span style="color: {THEME['text_primary']}; font-weight: 500;">{col['name']}</span>
                    <span style="color: {THEME['text_muted']}; font-size: 0.7rem;"> {col['type']}{pk}{nullable}</span>
                </div>
                """, unsafe_allow_html=True)

            if info.get("foreign_keys"):
                for fk in info["foreign_keys"]:
                    st.markdown(f"""
                    <div style="font-size: 0.72rem; color: {THEME['accent_primary']}; padding: 4px 0;">
                        🔗 {', '.join(fk['columns'])} → {fk['referred_table']}({', '.join(fk['referred_columns'])})
                    </div>
                    """, unsafe_allow_html=True)


def render_query_history_item(idx: int, question: str, sql: str, status: str = "success") -> bool:
    """Render a single history item. Returns True if clicked."""
    badge = render_status_badge("✓" if status == "success" else "✗", status)
    return st.button(
        f"{'🟢' if status == 'success' else '🔴'} {question[:50]}{'…' if len(question) > 50 else ''}",
        key=f"hist_{idx}",
        use_container_width=True,
    )


def render_empty_state(title: str, subtitle: str, icon: str = "💬"):
    st.markdown(f"""
    <div style="
        background: {THEME['bg_surface']};
        border: 1px solid {THEME['border']};
        border-radius: 16px;
        padding: 60px 40px;
        text-align: center;
        margin: 20px 0;
    ">
        <div style="font-size: 3rem; margin-bottom: 16px; opacity: 0.5;">{icon}</div>
        <h3 style="color: {THEME['text_primary']}; font-weight: 700; margin-bottom: 8px;">{title}</h3>
        <p style="color: {THEME['text_muted']}; font-size: 0.9rem; max-width: 450px; margin: 0 auto;">
            {subtitle}
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_error_banner(error: str):
    st.markdown(f"""
    <div style="
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-radius: 12px;
        padding: 16px 20px;
        color: {THEME['error']};
        font-size: 0.88rem;
        font-weight: 500;
    ">❌ {error}</div>
    """, unsafe_allow_html=True)


def render_safety_warning(warning: str):
    st.markdown(f"""
    <div style="
        background: rgba(245, 158, 11, 0.08);
        border: 1px solid rgba(245, 158, 11, 0.2);
        border-left: 3px solid {THEME['warning']};
        border-radius: 12px;
        padding: 16px 20px;
        color: {THEME['warning']};
        font-size: 0.88rem;
        font-weight: 500;
    ">🛡️ {warning}</div>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, icon: str = "📊", color: str = ""):
    accent = color or THEME['accent_primary']
    st.markdown(f"""
    <div style="
        background: {THEME['bg_surface']};
        border: 1px solid {THEME['border']};
        border-radius: 14px;
        padding: 18px;
        border-left: 3px solid {accent};
    ">
        <span style="float: right; font-size: 1.4rem; opacity: 0.6;">{icon}</span>
        <p style="margin: 0 0 4px 0; color: {THEME['text_muted']}; font-size: 0.72rem;
           font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{label}</p>
        <p style="margin: 0; color: {THEME['text_primary']}; font-size: 1.5rem;
           font-weight: 700; letter-spacing: -0.5px;">{value}</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_divider():
    st.markdown(f"""
    <div style="height: 1px; background: {THEME['border']}; margin: 16px 0; opacity: 0.5;"></div>
    """, unsafe_allow_html=True)


def render_footer():
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 32px 0 16px 0;
        color: {THEME['text_muted']};
        font-size: 0.75rem;
        border-top: 1px solid {THEME['border']};
        margin-top: 40px;
    ">
        🗣️ <strong style="color: {THEME['text_secondary']}">SpeakSQL</strong> v1.0 &nbsp;·&nbsp;
        Natural Language to SQL Copilot &nbsp;·&nbsp;
        Built with Streamlit & AI
    </div>
    """, unsafe_allow_html=True)


def render_loading_dots():
    st.markdown(f"""
    <div style="
        display: flex; align-items: center; gap: 8px;
        color: {THEME['text_muted']}; font-size: 0.85rem;
        padding: 12px 0;
    ">
        <div style="
            width: 8px; height: 8px; border-radius: 50%;
            background: {THEME['accent_primary']};
            animation: pulse 1.5s ease-in-out infinite;
        "></div>
        Processing...
    </div>
    <style>
        @keyframes pulse {{
            0%, 100% {{ opacity: 0.3; transform: scale(0.8); }}
            50% {{ opacity: 1; transform: scale(1.2); }}
        }}
    </style>
    """, unsafe_allow_html=True)
