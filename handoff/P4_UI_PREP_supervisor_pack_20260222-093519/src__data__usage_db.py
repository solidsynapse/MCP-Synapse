import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.data.usage_status import normalize_usage_status


class UsageDatabase:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self._root = Path(__file__).resolve().parents[2]
        if db_path is None:
            self._data_dir = self._root / "data"
            self._db_path = self._data_dir / "usage.db"
        else:
            resolved = Path(db_path).expanduser().resolve()
            self._data_dir = resolved.parent
            self._db_path = resolved
        self._ensure_storage()

    def _get_usage_columns(self, connection: sqlite3.Connection) -> set[str]:
        rows = connection.execute("PRAGMA table_info(usage)").fetchall()
        return {str(r[1]) for r in rows if len(r) > 1}

    def _ensure_storage(self) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS usage(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    tokens_input INTEGER NOT NULL,
                    tokens_output INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    latency_ms INTEGER,
                    status TEXT,
                    error_type TEXT,
                    request_id TEXT,
                    provider TEXT,
                    model_id TEXT
                )
                """
            )
            existing = self._get_usage_columns(connection)
            to_add = {
                "latency_ms": "INTEGER",
                "status": "TEXT",
                "error_type": "TEXT",
                "request_id": "TEXT",
                "provider": "TEXT",
                "model_id": "TEXT",
            }
            for col, col_type in to_add.items():
                if col in existing:
                    continue
                try:
                    connection.execute(f"ALTER TABLE usage ADD COLUMN {col} {col_type}")
                except Exception:
                    pass
            connection.commit()

    def log_usage(
        self,
        agent_id: str,
        agent_name: str,
        tokens_input: int,
        tokens_output: int,
        cost_usd: float,
        timestamp: str | None = None,
        latency_ms: int | None = None,
        status: str | None = None,
        error_type: str | None = None,
        request_id: str | None = None,
        provider: str | None = None,
        model_id: str | None = None,
    ) -> None:
        self._ensure_storage()
        recorded_at = timestamp or datetime.now(timezone.utc).isoformat()
        canonical_status, canonical_error_type = normalize_usage_status(status, error_type)
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                INSERT INTO usage(
                    timestamp,
                    agent_id,
                    agent_name,
                    tokens_input,
                    tokens_output,
                    cost_usd,
                    latency_ms,
                    status,
                    error_type,
                    request_id,
                    provider,
                    model_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    recorded_at,
                    agent_id,
                    agent_name,
                    int(tokens_input),
                    int(tokens_output),
                    float(cost_usd),
                    int(latency_ms) if latency_ms is not None else None,
                    canonical_status,
                    canonical_error_type,
                    request_id,
                    provider,
                    model_id,
                ),
            )
            connection.commit()

    def get_total_cost(self) -> float:
        self._ensure_storage()
        with sqlite3.connect(self._db_path) as connection:
            row = connection.execute("SELECT SUM(cost_usd) FROM usage").fetchone()
            return float(row[0] or 0.0)

    def get_recent_usage(self, limit: int = 10) -> list[dict]:
        self._ensure_storage()
        with sqlite3.connect(self._db_path) as connection:
            rows = connection.execute(
                """
                SELECT id,
                       timestamp,
                       agent_id,
                       agent_name,
                       tokens_input,
                       tokens_output,
                       cost_usd,
                       latency_ms,
                       status,
                       error_type,
                       request_id,
                       provider,
                       model_id
                FROM usage
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        results = []
        for row in rows:
            canonical_status, canonical_error_type = normalize_usage_status(
                row[8] if len(row) > 8 else None,
                row[9] if len(row) > 9 else None,
            )
            results.append(
                {
                    "id": row[0],
                    "timestamp": row[1],
                    "agent_id": row[2],
                    "agent_name": row[3],
                    "tokens_input": row[4],
                    "tokens_output": row[5],
                    "cost_usd": row[6],
                    "latency_ms": row[7] if len(row) > 7 else None,
                    "status": canonical_status,
                    "error_type": canonical_error_type,
                    "request_id": row[10] if len(row) > 10 else None,
                    "provider": row[11] if len(row) > 11 else None,
                    "model_id": row[12] if len(row) > 12 else None,
                }
            )
        return results

    def list_agent_names(
        self,
        start_timestamp: str | None = None,
        end_timestamp: str | None = None,
    ) -> list[str]:
        self._ensure_storage()
        where: list[str] = []
        params: list[object] = []
        if start_timestamp is not None:
            where.append("timestamp >= ?")
            params.append(str(start_timestamp))
        if end_timestamp is not None:
            where.append("timestamp < ?")
            params.append(str(end_timestamp))
        where_sql = ""
        if where:
            where_sql = " WHERE " + " AND ".join(where)
        with sqlite3.connect(self._db_path) as connection:
            rows = connection.execute(
                "SELECT DISTINCT agent_name FROM usage" + where_sql + " ORDER BY agent_name ASC",
                tuple(params),
            ).fetchall()
        return [str(r[0]) for r in rows if r and r[0]]

    def list_usage(
        self,
        agent_id: str | None = None,
        agent_name: str | None = None,
        start_timestamp: str | None = None,
        end_timestamp: str | None = None,
        limit: int = 200,
        most_recent: bool = False,
    ) -> list[dict]:
        self._ensure_storage()
        where: list[str] = []
        params: list[object] = []
        if agent_id is not None:
            where.append("agent_id = ?")
            params.append(str(agent_id))
        if agent_name is not None:
            where.append("agent_name = ?")
            params.append(str(agent_name))
        if start_timestamp is not None:
            where.append("timestamp >= ?")
            params.append(str(start_timestamp))
        if end_timestamp is not None:
            where.append("timestamp < ?")
            params.append(str(end_timestamp))
        where_sql = ""
        if where:
            where_sql = " WHERE " + " AND ".join(where)
        order_sql = " ORDER BY datetime(timestamp) ASC, request_id ASC, id ASC"
        if most_recent:
            order_sql = " ORDER BY datetime(timestamp) DESC, request_id DESC, id DESC"
        sql = (
            """
            SELECT id,
                   timestamp,
                   agent_id,
                   agent_name,
                   tokens_input,
                   tokens_output,
                   cost_usd,
                   latency_ms,
                   status,
                   error_type,
                   request_id,
                   provider,
                   model_id
            FROM usage
            """
            + where_sql
            + order_sql
            + " LIMIT ?"
        )
        params.append(int(limit))
        with sqlite3.connect(self._db_path) as connection:
            rows = connection.execute(sql, tuple(params)).fetchall()
        results: list[dict] = []
        for row in rows:
            canonical_status, canonical_error_type = normalize_usage_status(row[8], row[9])
            results.append(
                {
                    "id": row[0],
                    "timestamp": row[1],
                    "agent_id": row[2],
                    "agent_name": row[3],
                    "tokens_input": row[4],
                    "tokens_output": row[5],
                    "cost_usd": row[6],
                    "latency_ms": row[7],
                    "status": canonical_status,
                    "error_type": canonical_error_type,
                    "request_id": row[10],
                    "provider": row[11],
                    "model_id": row[12],
                }
            )
        return results

    def clear_usage(self) -> None:
        self._ensure_storage()
        with sqlite3.connect(self._db_path) as connection:
            connection.execute("DELETE FROM usage")
            connection.commit()

    def close(self) -> None:
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
