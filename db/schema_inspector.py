"""
SpeakSQL — Database schema inspector.
Introspects tables, columns, foreign keys, and sample rows for LLM context.
"""

import pandas as pd
from sqlalchemy import inspect as sa_inspect, text


def inspect_schema(engine) -> dict:
    """
    Introspect database schema: tables, columns, primary keys, foreign keys, and sample rows.

    Args:
        engine: SQLAlchemy engine instance

    Returns:
        dict mapping table_name → {columns, primary_key, foreign_keys, sample_rows, row_count}
    """
    inspector = sa_inspect(engine)
    schema = {}

    for table_name in inspector.get_table_names():
        # Columns
        columns = []
        for col in inspector.get_columns(table_name):
            columns.append({
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "default": str(col.get("default", "")) if col.get("default") else None,
            })

        # Primary key
        pk = inspector.get_pk_constraint(table_name)
        primary_key = pk.get("constrained_columns", []) if pk else []

        # Foreign keys
        fks = []
        for fk in inspector.get_foreign_keys(table_name):
            fks.append({
                "columns": fk.get("constrained_columns", []),
                "referred_table": fk.get("referred_table", ""),
                "referred_columns": fk.get("referred_columns", []),
            })

        # Sample rows (first 3)
        sample_rows = []
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f'SELECT * FROM "{table_name}" LIMIT 3'))
                rows = result.fetchall()
                col_names = list(result.keys())
                for row in rows:
                    sample_rows.append(dict(zip(col_names, [str(v) for v in row])))
        except Exception:
            pass

        # Row count
        row_count = 0
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                row_count = result.scalar() or 0
        except Exception:
            pass

        schema[table_name] = {
            "columns": columns,
            "primary_key": primary_key,
            "foreign_keys": fks,
            "sample_rows": sample_rows,
            "row_count": row_count,
        }

    return schema


def format_schema_for_llm(schema: dict) -> str:
    """
    Format the schema dict into a clear text representation for the LLM system prompt.

    Args:
        schema: Schema dict from inspect_schema()

    Returns:
        Formatted string with table definitions, relationships, and sample data.
    """
    parts = []
    parts.append("DATABASE SCHEMA")
    parts.append("=" * 60)

    for table_name, info in schema.items():
        parts.append(f"\n── Table: {table_name} ({info['row_count']} rows) ──")

        # Columns
        parts.append("  Columns:")
        for col in info["columns"]:
            pk_marker = " [PK]" if col["name"] in info["primary_key"] else ""
            nullable = "" if col["nullable"] else " NOT NULL"
            parts.append(f"    • {col['name']} ({col['type']}){pk_marker}{nullable}")

        # Foreign keys
        if info["foreign_keys"]:
            parts.append("  Foreign Keys:")
            for fk in info["foreign_keys"]:
                cols = ", ".join(fk["columns"])
                ref_cols = ", ".join(fk["referred_columns"])
                parts.append(f"    → {cols} → {fk['referred_table']}({ref_cols})")

        # Sample rows
        if info["sample_rows"]:
            parts.append("  Sample Data (first 3 rows):")
            for i, row in enumerate(info["sample_rows"], 1):
                row_str = ", ".join([f"{k}={v}" for k, v in list(row.items())[:6]])
                parts.append(f"    [{i}] {row_str}")

    parts.append("\n" + "=" * 60)
    return "\n".join(parts)


def get_schema_summary(schema: dict) -> dict:
    """
    Get a quick summary: total tables, total columns, relationships count.
    """
    total_tables = len(schema)
    total_columns = sum(len(info["columns"]) for info in schema.values())
    total_rows = sum(info["row_count"] for info in schema.values())
    total_fks = sum(len(info["foreign_keys"]) for info in schema.values())

    return {
        "tables": total_tables,
        "columns": total_columns,
        "rows": total_rows,
        "relationships": total_fks,
    }
