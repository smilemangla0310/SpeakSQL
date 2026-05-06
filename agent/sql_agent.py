"""
SpeakSQL — Main NL→SQL orchestrator.
Pipeline: question → LLM generates SQL → safety check → execute → explain → suggest charts.
"""

import io
import time
import pandas as pd
from dataclasses import dataclass, field
from typing import Callable

from agent.llm_providers import create_provider, LLMProvider
from agent.prompts import (
    SQL_SYSTEM_PROMPT, EXPLANATION_SYSTEM_PROMPT, ERROR_FIX_SYSTEM_PROMPT,
    build_sql_prompt, build_explanation_prompt, build_error_fix_prompt,
    extract_sql_from_response,
)
from agent.safety import SQLSafetyFilter
from agent.memory import ConversationMemory


@dataclass
class QueryResponse:
    """Complete response from the SQL agent pipeline."""
    question: str = ""
    sql: str = ""
    df: pd.DataFrame | None = None
    row_count: int = 0
    truncated: bool = False
    execution_time: float = 0.0
    explanation: str = ""
    quick_stats: dict = field(default_factory=dict)
    column_types: dict = field(default_factory=dict)
    status_messages: list[str] = field(default_factory=list)
    error: str = ""
    safety_warning: str = ""
    attempts: int = 0


class SQLAgent:
    """
    Main AI agent for natural language to SQL translation.
    Manages the full pipeline: understand → generate SQL → safety check → execute → explain.
    """

    def __init__(
        self,
        db_manager,
        schema_str: str,
        provider_key: str = "groq",
        api_key: str = "",
        model_name: str = "llama-3.3-70b-versatile",
        temperature: float = 0.1,
        max_retries: int = 3,
        row_limit: int = 500,
    ):
        if not api_key:
            raise ValueError("API key is required.")

        self.db_manager = db_manager
        self.schema_str = schema_str
        self.provider = create_provider(provider_key, api_key, model_name)
        self.temperature = temperature
        self.max_retries = max_retries
        self.row_limit = row_limit
        self.safety = SQLSafetyFilter(max_row_limit=row_limit)
        self.memory = ConversationMemory()

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        return self.provider.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self.temperature,
            max_tokens=4096,
        )

    def generate_sql(self, question: str) -> str:
        """Generate SQL from a natural language question."""
        context = self.memory.get_context()
        prompt = build_sql_prompt(question, self.schema_str, context)
        response = self._call_llm(SQL_SYSTEM_PROMPT, prompt)
        return extract_sql_from_response(response)

    def explain_results(self, question: str, sql: str, df: pd.DataFrame) -> str:
        """Generate a plain-English explanation of query results."""
        # Build a text summary of the results
        buf = io.StringIO()
        if len(df) > 0:
            df.head(20).to_string(buf=buf)
            summary = f"Rows returned: {len(df)}\n\n{buf.getvalue()}"
        else:
            summary = "No rows returned."

        prompt = build_explanation_prompt(question, sql, summary)
        return self._call_llm(EXPLANATION_SYSTEM_PROMPT, prompt)

    def full_pipeline(
        self,
        question: str,
        status_callback: Callable[[str], None] | None = None,
    ) -> QueryResponse:
        """
        Run the full NL→SQL pipeline:
        1. Check for destructive intent
        2. Generate SQL via LLM
        3. Safety-check the SQL
        4. Execute against DB
        5. Generate explanation
        """
        resp = QueryResponse(question=question)

        def emit(msg: str):
            resp.status_messages.append(msg)
            if status_callback:
                status_callback(msg)

        try:
            # ── Step 0: Check destructive intent ─────────────────────
            is_destructive, warning = self.safety.check_destructive_intent(question)
            if is_destructive:
                resp.safety_warning = warning
                resp.error = warning
                emit("🚫 Destructive query detected — refused.")
                return resp

            # ── Step 1: Generate SQL ─────────────────────────────────
            emit("🧠 Generating SQL from your question...")
            sql = self.generate_sql(question)
            resp.sql = sql
            emit("✅ SQL generated")

            # ── Step 2: Safety check ─────────────────────────────────
            emit("🔒 Running safety checks...")
            is_safe, reason = self.safety.is_safe(sql)
            if not is_safe:
                resp.error = reason
                resp.safety_warning = reason
                emit(f"🚫 Safety check failed: {reason}")
                return resp
            emit("✅ Safety checks passed")

            # ── Step 3: Execute with retry loop ──────────────────────
            current_sql = sql
            db_result = None

            for attempt in range(1, self.max_retries + 1):
                resp.attempts = attempt
                emit(f"⚡ Executing query (attempt {attempt}/{self.max_retries})...")

                db_result = self.db_manager.execute_query(
                    current_sql, row_limit=self.row_limit
                )

                if db_result["error"] is None:
                    emit("✅ Query executed successfully")
                    break
                else:
                    emit(f"⚠️ Error: {db_result['error'][:100]}")

                    if attempt < self.max_retries:
                        emit("🔧 Asking AI to fix the query...")
                        fix_prompt = build_error_fix_prompt(
                            current_sql, db_result["error"], self.schema_str
                        )
                        fix_response = self._call_llm(ERROR_FIX_SYSTEM_PROMPT, fix_prompt)
                        current_sql = extract_sql_from_response(fix_response)
                        resp.sql = current_sql

                        # Re-check safety on fixed SQL
                        is_safe, reason = self.safety.is_safe(current_sql)
                        if not is_safe:
                            resp.error = f"Fixed SQL failed safety check: {reason}"
                            return resp
                    else:
                        emit("❌ Query failed after all attempts")

            if db_result is None or db_result["error"]:
                resp.error = db_result["error"] if db_result else "Unknown error"
                self.memory.add_turn(question, resp.sql, f"Error: {resp.error}")
                return resp

            # Store results
            resp.df = db_result["df"]
            resp.row_count = db_result["row_count"]
            resp.truncated = db_result["truncated"]
            resp.execution_time = db_result["execution_time"]
            resp.column_types = db_result["column_types"]

            # Quick stats
            if resp.df is not None and len(resp.df) > 0:
                resp.quick_stats = self.db_manager.get_quick_stats(resp.df)

            # ── Step 4: Generate explanation ─────────────────────────
            emit("💡 Generating insights...")
            try:
                resp.explanation = self.explain_results(question, resp.sql, resp.df)
                emit("✅ Insights ready")
            except Exception as e:
                resp.explanation = f"Could not generate explanation: {e}"
                emit("⚠️ Explanation generation failed")

            emit("🎉 Analysis complete!")

            # ── Step 5: Update memory ────────────────────────────────
            result_summary = f"{resp.row_count} rows returned"
            if resp.df is not None and len(resp.df) > 0:
                result_summary += f". Columns: {', '.join(resp.df.columns[:5])}"
            self.memory.add_turn(question, resp.sql, result_summary)

        except Exception as e:
            resp.error = f"Agent error: {str(e)}"
            emit(f"❌ Error: {str(e)}")

        return resp

    def run_custom_sql(self, sql: str) -> QueryResponse:
        """Execute user-edited SQL directly (with safety checks)."""
        resp = QueryResponse(sql=sql)

        is_safe, reason = self.safety.is_safe(sql)
        if not is_safe:
            resp.error = reason
            resp.safety_warning = reason
            return resp

        db_result = self.db_manager.execute_query(sql, row_limit=self.row_limit)
        if db_result["error"]:
            resp.error = db_result["error"]
            return resp

        resp.df = db_result["df"]
        resp.row_count = db_result["row_count"]
        resp.truncated = db_result["truncated"]
        resp.execution_time = db_result["execution_time"]
        resp.column_types = db_result["column_types"]

        if resp.df is not None and len(resp.df) > 0:
            resp.quick_stats = self.db_manager.get_quick_stats(resp.df)

        return resp

    def clear_memory(self):
        self.memory.clear()
