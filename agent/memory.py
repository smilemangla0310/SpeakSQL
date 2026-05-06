"""
SpeakSQL — Conversation memory for follow-up questions.
"""


class ConversationMemory:
    """
    Maintains conversation context so the user can ask follow-ups
    like "Now filter only HR" or "Sort by revenue descending."
    """

    def __init__(self, max_turns: int = 8):
        self.max_turns = max_turns
        self.turns: list[dict] = []

    def add_turn(self, question: str, sql: str = "", result_summary: str = ""):
        """Add a conversation turn."""
        self.turns.append({
            "question": question,
            "sql": sql,
            "result_summary": result_summary[:500],
        })
        # Keep only last N turns
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]

    def get_context(self) -> str:
        """Get formatted conversation context for the LLM prompt."""
        if not self.turns:
            return ""

        parts = []
        for i, turn in enumerate(self.turns, 1):
            parts.append(f"Turn {i}:")
            parts.append(f"  Question: {turn['question']}")
            if turn['sql']:
                parts.append(f"  SQL: {turn['sql'][:300]}")
            if turn['result_summary']:
                parts.append(f"  Result: {turn['result_summary'][:200]}")
        return "\n".join(parts)

    def get_last_sql(self) -> str:
        """Get the last generated SQL query."""
        if self.turns:
            return self.turns[-1].get("sql", "")
        return ""

    def clear(self):
        """Reset conversation memory."""
        self.turns.clear()
