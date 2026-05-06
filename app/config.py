"""
SpeakSQL — App configuration, design tokens, and provider settings.
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── App Settings ──────────────────────────────────────────────────────────────
APP_TITLE = "SpeakSQL"
APP_ICON = "🗣️"
APP_SUBTITLE = "Natural Language to SQL Copilot"
APP_VERSION = "1.0"

# ── Design Tokens (Teal/Cyan Dark Theme) ─────────────────────────────────────
THEME = {
    # Backgrounds — light buttery surfaces
    "bg_primary": "#FCFBF4",
    "bg_surface": "#FFFDF2",
    "bg_surface_hover": "#F5F2E6",
    "bg_elevated": "#FFFFFF",
    "bg_card": "#FFFFFF",
    # Borders
    "border": "#E5E1D8",
    "border_accent": "#D6D1C4",
    # Accent Colors — engaging warm orange and blue
    "accent_primary": "#F59E0B",       # Amber/Orange
    "accent_secondary": "#3B82F6",     # Blue
    "accent_tertiary": "#10B981",      # Emerald
    "accent_gradient": "linear-gradient(135deg, #F59E0B 0%, #EAB308 50%, #EF4444 100%)",
    "accent_gradient_subtle": "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)",
    # Status
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "info": "#3B82F6",
    # Text
    "text_primary": "#1E293B",
    "text_secondary": "#475569",
    "text_muted": "#64748B",
    "text_accent": "#B45309",
    # SQL Syntax Highlighting
    "sql_keyword": "#2563EB",
    "sql_string": "#059669",
    "sql_number": "#D97706",
    "sql_comment": "#94A3B8",
    # Glow Effects
    "glow_primary": "0 4px 14px 0 rgba(245, 158, 11, 0.39)",
    "glow_accent": "0 4px 14px 0 rgba(59, 130, 246, 0.39)",
    "glow_success": "0 4px 14px 0 rgba(16, 185, 129, 0.39)",
}

# ── LLM Provider Settings ────────────────────────────────────────────────────
LLM_PROVIDERS = {
    "Groq (Free)": {
        "key": "groq",
        "env_var": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ],
        "help": "Free key → https://console.groq.com/keys (14,400 req/day)",
    },
    "HuggingFace (Free)": {
        "key": "huggingface",
        "env_var": "HF_API_KEY",
        "default_model": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "models": [
            "Qwen/Qwen2.5-Coder-32B-Instruct",
            "mistralai/Mistral-Small-24B-Instruct-2501",
            "meta-llama/Llama-3.3-70B-Instruct",
        ],
        "help": "Free token → https://huggingface.co/settings/tokens",
    },
    "Google Gemini": {
        "key": "gemini",
        "env_var": "GOOGLE_API_KEY",
        "default_model": "gemini-2.0-flash",
        "models": [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ],
        "help": "Free key → https://aistudio.google.com/apikey",
    },
}

DEFAULT_PROVIDER = "Groq (Free)"
TEMPERATURE = 0.1
MAX_RETRIES = 3

# ── Database Settings ─────────────────────────────────────────────────────────
DEMO_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db", "demo.db")
DEFAULT_ROW_LIMIT = 500
QUERY_TIMEOUT = 30  # seconds

# ── Env Key Loader ────────────────────────────────────────────────────────────
def get_secret(key_name):
    """Load a secret from .env, OS environment, or Streamlit secrets."""
    val = os.getenv(key_name, "")
    if val:
        return val
    try:
        return st.secrets.get(key_name, "")
    except Exception:
        return ""

GROQ_API_KEY = get_secret("GROQ_API_KEY")
HF_API_KEY = get_secret("HF_API_KEY")
GOOGLE_API_KEY = get_secret("GOOGLE_API_KEY")

# ── Sample Questions ──────────────────────────────────────────────────────────
SAMPLE_QUERIES = [
    ("👥", "List all employees with their department names and salaries"),
    ("💰", "What is the average salary by department?"),
    ("📈", "Show total sales revenue by month for 2024"),
    ("🏆", "Which are the top 5 best-selling products?"),
    ("🌍", "Compare total order amounts by customer city"),
    ("📊", "Show employee count per department as a bar chart"),
    ("🔗", "List orders with customer name, product, and total amount"),
    ("📉", "What is the monthly revenue trend from 2023 to 2024?"),
]

# ── Page Config ───────────────────────────────────────────────────────────────
PAGE_CONFIG = {
    "page_title": f"{APP_TITLE} — {APP_SUBTITLE}",
    "page_icon": APP_ICON,
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}
