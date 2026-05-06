# 🗣️ SpeakSQL — Natural Language to SQL Copilot

**Talk to your database in plain English.** SpeakSQL translates natural language questions into safe, schema-aware SQL queries, executes them, and shows you results with auto-generated charts and AI-powered explanations.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## ✨ Features

- **🧠 Schema-Aware NL→SQL** — LLM reads your database schema (tables, columns, FKs, sample rows) and generates accurate SQL
- **🔒 Safety First** — Only SELECT/WITH queries allowed; DDL/DML is blocked with clear warnings
- **📊 Auto Charts** — Plotly charts auto-suggested based on result shape (bar, line, scatter, pie, histogram, heatmap)
- **💡 AI Insights** — Plain-English explanation of results with key findings highlighted
- **✏️ Edit & Re-Run** — Review and edit generated SQL before execution
- **🔄 Follow-up Questions** — Conversation memory for contextual follow-ups
- **🕘 Query History** — Clickable history to re-run past queries
- **🔍 Schema Browser** — Explore tables, columns, types, and relationships in the sidebar
- **🎨 Premium Dark UI** — Professional dashboard with teal/cyan accent theme

---

## 🏗️ Architecture

```
User Question → LLM (Groq) → SQL Generation → Safety Filter → DB Execution → Results + Charts + Explanation
```

```
SpeakSQL/
├── app/
│   ├── config.py            # Design tokens, constants
│   ├── main.py              # Streamlit entry point
│   └── ui_components.py     # Premium dark-theme components
├── agent/
│   ├── llm_providers.py     # Groq / HuggingFace / Gemini
│   ├── sql_agent.py         # NL→SQL orchestrator
│   ├── prompts.py           # System prompts
│   ├── safety.py            # SQL safety filter
│   └── memory.py            # Conversation memory
├── db/
│   ├── connection.py        # SQLAlchemy engine
│   ├── schema_inspector.py  # Schema introspection
│   ├── seed_demo.py         # Demo DB seeder
│   └── demo.db              # Pre-seeded SQLite
└── viz/
    └── chart_engine.py      # Auto-suggest & render charts
```

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/your-username/SpeakSQL.git
cd SpeakSQL
pip install -r requirements.txt
```

### 2. Add API Key
```bash
cp .env.example .env
# Edit .env and add your Groq API key (free from https://console.groq.com/keys)
```

### 3. Run
```bash
streamlit run app/main.py
```

The demo database (HR + Sales, 7 tables, ~500 rows) is auto-created on first launch.

---

## 💬 Example Questions to Try

| Category | Question |
|----------|----------|
| 👥 HR | "List all employees with their department names and salaries" |
| 💰 Salary | "What is the average salary by department?" |
| 📈 Trends | "Show total sales revenue by month for 2024" |
| 🏆 Ranking | "Which are the top 5 best-selling products?" |
| 🌍 Geography | "Compare total order amounts by customer city" |
| 📊 Charts | "Show employee count per department as a bar chart" |
| 🔗 Joins | "List orders with customer name, product, and total amount" |
| 📉 Comparison | "What is the monthly revenue trend from 2023 to 2024?" |

---

## 🔒 Safety Constraints

- **Read-only**: Only `SELECT` and `WITH` (CTE) statements are allowed
- **Blocked operations**: `DROP`, `CREATE`, `ALTER`, `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `GRANT`, `REVOKE`, `EXEC`
- **Injection protection**: Multi-statement queries, SQL comments, and suspicious patterns are blocked
- **Row limits**: Results capped at 500 rows with truncation warning
- **Destructive intent detection**: Natural language requests for data modification are refused with explanation

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| UI | Streamlit (dark theme) |
| LLM | Groq (llama-3.3-70b) — free tier |
| Database | SQLite via SQLAlchemy |
| Charts | Plotly (interactive) |
| Data | pandas, numpy |

---

## 📄 License

MIT License — feel free to use, modify, and distribute.
