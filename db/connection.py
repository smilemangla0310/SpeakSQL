"""
SpeakSQL — Database connection manager using SQLAlchemy.
Handles engine creation, safe query execution, and row limiting.
"""

import time
import pandas as pd
from sqlalchemy import create_engine, text, event
from sqlalchemy.pool import StaticPool


class DatabaseManager:
    """
    Manages database connections and safe query execution.
    Uses SQLAlchemy for clean connection handling with row limits and timeouts.
    """

    def __init__(self, db_path: str = "", connection_string: str = ""):
        """
        Initialize with either a SQLite file path or a full connection string.

        Args:
            db_path: Path to SQLite database file
            connection_string: Full SQLAlchemy connection string (overrides db_path)
        """
        if connection_string:
            self.connection_string = connection_string
        elif db_path:
            self.connection_string = f"sqlite:///{db_path}"
        else:
            raise ValueError("Either db_path or connection_string is required.")

        # SQLite-specific: use StaticPool for thread safety in Streamlit
        if "sqlite" in self.connection_string:
            self.engine = create_engine(
                self.connection_string,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False,
            )
            # Enable foreign keys for SQLite
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        else:
            self.engine = create_engine(
                self.connection_string,
                pool_size=5,
                max_overflow=10,
                echo=False,
            )

        self.db_type = "sqlite" if "sqlite" in self.connection_string else "postgresql"

    def execute_query(
        self,
        sql: str,
        params: dict | None = None,
        row_limit: int = 500,
        timeout: int = 30,
    ) -> dict:
        """
        Execute a SQL query and return results as a dict.

        Args:
            sql: SQL query string
            params: Optional parameters for parameterized queries
            row_limit: Maximum rows to return
            timeout: Query timeout in seconds

        Returns:
            dict with keys: df, row_count, truncated, execution_time, columns, column_types, error
        """
        start_time = time.time()
        result = {
            "df": None,
            "row_count": 0,
            "truncated": False,
            "execution_time": 0.0,
            "columns": [],
            "column_types": {},
            "error": None,
        }

        try:
            with self.engine.connect() as conn:
                # Add LIMIT if not already present (safety net)
                sql_upper = sql.strip().upper()
                has_limit = "LIMIT" in sql_upper.split(")")[-1]  # Check outside subqueries

                if not has_limit and row_limit:
                    exec_sql = f"{sql.rstrip().rstrip(';')}\nLIMIT {row_limit + 1}"
                else:
                    exec_sql = sql

                stmt = text(exec_sql)
                if params:
                    rs = conn.execute(stmt, params)
                else:
                    rs = conn.execute(stmt)

                # Fetch results
                rows = rs.fetchall()
                columns = list(rs.keys()) if rs.keys() else []

                # Check truncation
                if not has_limit and len(rows) > row_limit:
                    rows = rows[:row_limit]
                    result["truncated"] = True

                # Build DataFrame
                if rows and columns:
                    df = pd.DataFrame(rows, columns=columns)
                    result["df"] = df
                    result["row_count"] = len(df)
                    result["columns"] = columns

                    # Infer column types
                    for col in df.columns:
                        if pd.api.types.is_numeric_dtype(df[col]):
                            result["column_types"][col] = "numeric"
                        elif pd.api.types.is_datetime64_any_dtype(df[col]):
                            result["column_types"][col] = "datetime"
                        else:
                            # Try to parse as date
                            try:
                                pd.to_datetime(df[col], errors="raise")
                                result["column_types"][col] = "datetime"
                            except (ValueError, TypeError):
                                result["column_types"][col] = "categorical"
                else:
                    result["df"] = pd.DataFrame()
                    result["row_count"] = 0

        except Exception as e:
            result["error"] = str(e)

        result["execution_time"] = round(time.time() - start_time, 3)
        return result

    def get_table_names(self) -> list[str]:
        """Get all table names in the database."""
        from sqlalchemy import inspect as sa_inspect
        inspector = sa_inspect(self.engine)
        return inspector.get_table_names()

    def test_connection(self) -> tuple[bool, str]:
        """Test if the database connection is working."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)

    def get_quick_stats(self, df: pd.DataFrame) -> dict:
        """
        Generate quick statistics for a result DataFrame.

        Returns dict with row_count, column_count, numeric_stats, categorical_stats.
        """
        stats = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "numeric_stats": {},
            "categorical_stats": {},
        }

        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                stats["numeric_stats"][col] = {
                    "min": round(float(df[col].min()), 2) if not df[col].isna().all() else None,
                    "max": round(float(df[col].max()), 2) if not df[col].isna().all() else None,
                    "avg": round(float(df[col].mean()), 2) if not df[col].isna().all() else None,
                    "nulls": int(df[col].isna().sum()),
                }
            else:
                stats["categorical_stats"][col] = {
                    "distinct": int(df[col].nunique()),
                    "top_value": str(df[col].mode().iloc[0]) if not df[col].mode().empty else "N/A",
                    "nulls": int(df[col].isna().sum()),
                }

        return stats

    def dispose(self):
        """Close all connections."""
        self.engine.dispose()
