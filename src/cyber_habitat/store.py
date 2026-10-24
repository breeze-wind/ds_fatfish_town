import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .domain import WorldEvent


class SQLiteEventStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.path)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.execute("""CREATE TABLE IF NOT EXISTS world_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurred_at TEXT NOT NULL,
            event_type TEXT NOT NULL,
            subject TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )""")
        self._db.commit()

    def append(self, event_type: str, subject: str, payload: dict[str, object]) -> WorldEvent:
        occurred_at = datetime.now(timezone.utc).isoformat()
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        cursor = self._db.execute(
            "INSERT INTO world_events (occurred_at, event_type, subject, payload_json) VALUES (?, ?, ?, ?)",
            (occurred_at, event_type, subject, encoded),
        )
        self._db.commit()
        return WorldEvent(cursor.lastrowid, occurred_at, event_type, subject, payload)

    def list_events(self) -> list[WorldEvent]:
        rows = self._db.execute(
            "SELECT id, occurred_at, event_type, subject, payload_json FROM world_events ORDER BY id"
        ).fetchall()
        return [WorldEvent(row["id"], row["occurred_at"], row["event_type"], row["subject"],
                           json.loads(row["payload_json"])) for row in rows]

    def close(self) -> None:
        self._db.close()
