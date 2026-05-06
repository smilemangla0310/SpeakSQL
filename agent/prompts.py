"""
SpeakSQL — System prompts and prompt builders for the NL→SQL agent.
"""

SQL_SYSTEM_PROMPT = """You are SpeakSQL, an expert SQL assistant. You translate natural language questions into safe, well-formatted SQL queries.

RULES:
1. Generate ONLY read-only SQL: SELECT statements and WITH (CTEs). Nothing else.
2. NEVER generate DDL or DML: no DROP, CREATE, ALTER, TRUNCATE, INSERT, UPDATE, DELETE, GRANT, REVOKE, EXEC.
3. If the user asks for a destructive operation, REFUSE explicitly and explain why.
4. Always match column and table names EXACTLY as shown in the schema. Use quotes if names have spaces.
5. Use proper JOINs when querying across tables. Prefer explicit JOIN syntax over implicit.
6. Use aliases for readability. Format SQL with proper indentation.
7. For aggregations, always include GROUP BY. For ordering, use ORDER BY.
8. When the user asks for "top N", use LIMIT N.
9. Use COALESCE for nullable columns in calculations.
10. Return ONLY the SQL query inside a ```sql code block. No explanations before or after.

EXAMPLE OUTPUT:
```sql
SELECT 
    d.department_name,
    COUNT(e.employee_id) AS employee_count,
    ROUND(AVG(s.amount), 2) AS avg_salary
FROM employees e
JOIN departments d ON e.department_id = d.department_id
JOIN salaries s ON e.employee_id = s.employee_id
GROUP BY d.department_name
ORDER BY avg_salary DESC;
```
"""

EXPLANATION_SYSTEM_PROMPT = """You are SpeakSQL's insight engine. Given a SQL query and its results, provide a clear, concise explanation in plain English.

RULES:
1. Start with a one-sentence summary of what the query does.
2. Highlight key findings: top values, trends, comparisons, anomalies.
3. Use bullet points for multiple insights.
4. Mention specific numbers from the results.
5. If results are empty, explain possible reasons.
6. Keep it under 150 words.
7. Use a professional, analytical tone.
"""

ERROR_FIX_SYSTEM_PROMPT = """You are SpeakSQL's error-correction engine. The previous SQL query failed with an error.
Analyze the error message and the original SQL, then generate a CORRECTED SQL query.

RULES:
1. Fix only what's broken — keep the original intent.
2. Common fixes: wrong column names, missing JOINs, syntax errors, type mismatches.
3. Return ONLY the corrected SQL in a ```sql code block.
4. The query must still be read-only (SELECT/WITH only).
"""


def build_sql_prompt(question: str, schema_str: str, conversation_context: str = "") -> str:
    """Build the user prompt for SQL generation."""
    parts = [f"DATABASE SCHEMA:\n{schema_str}"]
    if conversation_context:
        parts.append(f"\nCONVERSATION CONTEXT (previous queries for follow-up reference):\n{conversation_context}")
    parts.append(f"\nUSER QUESTION: {question}")
    parts.append("\nGenerate the SQL query:")
    return "\n".join(parts)


def build_explanation_prompt(question: str, sql: str, results_summary: str) -> str:
    """Build the user prompt for result explanation."""
    return f"""USER QUESTION: {question}

SQL QUERY EXECUTED:
```sql
{sql}
```

QUERY RESULTS:
{results_summary}

Provide a clear, insightful explanation of these results:"""


def build_error_fix_prompt(original_sql: str, error_message: str, schema_str: str) -> str:
    """Build prompt to fix a failed SQL query."""
    return f"""DATABASE SCHEMA:
{schema_str}

ORIGINAL SQL THAT FAILED:
```sql
{original_sql}
```

ERROR MESSAGE:
{error_message}

Generate the corrected SQL query:"""


def extract_sql_from_response(response: str) -> str:
    """Extract SQL from LLM response (handles code blocks)."""
    # Try to extract from ```sql ... ``` blocks
    if "```sql" in response:
        parts = response.split("```sql")
        if len(parts) > 1:
            sql = parts[1].split("```")[0].strip()
            return sql
    # Try generic code blocks
    if "```" in response:
        parts = response.split("```")
        if len(parts) >= 3:
            sql = parts[1].strip()
            # Remove language tag if present
            if sql.startswith("sql\n") or sql.startswith("SQL\n"):
                sql = sql[4:]
            return sql.strip()
    # Return as-is (might already be raw SQL)
    return response.strip()
