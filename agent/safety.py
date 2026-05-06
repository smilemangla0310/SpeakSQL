"""
SpeakSQL — SQL safety filter.
Blocks destructive DDL/DML statements, enforces read-only access.
"""

import re


# Patterns that indicate destructive/unsafe SQL
BLOCKED_KEYWORDS = [
    r'\bDROP\b', r'\bTRUNCATE\b', r'\bALTER\b', r'\bCREATE\b',
    r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b', r'\bREPLACE\b',
    r'\bGRANT\b', r'\bREVOKE\b', r'\bEXEC\b', r'\bEXECUTE\b',
    r'\bMERGE\b', r'\bCALL\b', r'\bSET\b',
    r'\bATTACH\b', r'\bDETACH\b', r'\bVACUUM\b', r'\bREINDEX\b',
    r'\bPRAGMA\b',
]

# Additional dangerous patterns
BLOCKED_PATTERNS = [
    r';\s*(DROP|ALTER|CREATE|INSERT|UPDATE|DELETE|TRUNCATE)',  # Multi-statement attacks
    r'--\s*$',  # SQL comment at end (potential injection)
    r'/\*.*\*/',  # Block comments (potential injection hiding)
    r'INTO\s+OUTFILE',  # File writes
    r'LOAD\s+DATA',  # File reads
    r'xp_\w+',  # SQL Server extended procedures
]


class SQLSafetyFilter:
    """
    Validates SQL queries for safety before execution.
    Only allows SELECT and WITH (CTE) statements.
    """

    def __init__(self, max_row_limit: int = 500):
        self.max_row_limit = max_row_limit
        self._blocked_re = [re.compile(p, re.IGNORECASE) for p in BLOCKED_KEYWORDS]
        self._pattern_re = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in BLOCKED_PATTERNS]

    def is_safe(self, sql: str) -> tuple[bool, str]:
        """
        Check if a SQL query is safe to execute.

        Args:
            sql: The SQL query string

        Returns:
            (is_safe, reason) — True if safe, False with explanation if not
        """
        if not sql or not sql.strip():
            return False, "Empty query."

        cleaned = sql.strip()

        # Check for multiple statements (semicolons not in strings)
        statements = self._split_statements(cleaned)
        if len(statements) > 1:
            return False, "⚠️ Multiple SQL statements detected. Only single queries are allowed."

        # Remove string literals for keyword scanning
        no_strings = re.sub(r"'[^']*'", "''", cleaned)
        no_strings = re.sub(r'"[^"]*"', '""', no_strings)

        # Check blocked keywords
        for pattern in self._blocked_re:
            match = pattern.search(no_strings)
            if match:
                keyword = match.group(0).upper()
                return False, f"🚫 Blocked: {keyword} statements are not allowed. SpeakSQL only supports read-only queries (SELECT/WITH)."

        # Check blocked patterns
        for pattern in self._pattern_re:
            if pattern.search(no_strings):
                return False, "🚫 Potentially unsafe SQL pattern detected."

        # Verify it starts with SELECT or WITH
        upper = no_strings.strip().upper()
        if not (upper.startswith("SELECT") or upper.startswith("WITH") or upper.startswith("(")):
            return False, f"🚫 Query must start with SELECT or WITH. Got: {upper[:20]}..."

        return True, "✅ Query passed safety checks."

    def _split_statements(self, sql: str) -> list[str]:
        """Split SQL by semicolons, ignoring those inside string literals."""
        in_single = False
        in_double = False
        statements = []
        current = []

        for char in sql:
            if char == "'" and not in_double:
                in_single = not in_single
            elif char == '"' and not in_single:
                in_double = not in_double
            elif char == ';' and not in_single and not in_double:
                stmt = ''.join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
                continue
            current.append(char)

        last = ''.join(current).strip()
        if last:
            statements.append(last)

        return statements

    def check_destructive_intent(self, question: str) -> tuple[bool, str]:
        """
        Check if the user's natural language question asks for destructive operations.
        Returns (is_destructive, warning_message).
        """
        destructive_patterns = [
            (r'\b(delete|remove|drop|destroy|erase|wipe)\b.*\b(table|database|record|row|data)\b', "delete data"),
            (r'\b(update|modify|change|edit|alter)\b.*\b(table|column|record|row|value)\b', "modify data"),
            (r'\b(insert|add|create)\b.*\b(table|record|row|entry)\b', "insert data"),
            (r'\b(truncate|purge|clear)\b', "clear data"),
        ]
        q_lower = question.lower()
        for pattern, action in destructive_patterns:
            if re.search(pattern, q_lower):
                return True, (
                    f"⚠️ It looks like you're asking to **{action}**. "
                    f"SpeakSQL is a read-only assistant — I can only help you **query and analyze** data. "
                    f"I cannot modify the database. Try rephrasing as a SELECT query!"
                )
        return False, ""
