import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .domain import Resident, WorldEvent

SCHEMA_VERSION = 2


class SQLiteEventStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        # The HTTP server opens the store before starting its single request thread.
        # Calls remain serialized by the standard-library HTTPServer.
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.execute("""CREATE TABLE IF NOT EXISTS world_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurred_at TEXT NOT NULL,
            event_type TEXT NOT NULL,
            subject TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )""")
        self._migrate()
        self._db.commit()

    def _migrate(self) -> None:
        version = self._db.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise RuntimeError(f"database schema {version} is newer than supported {SCHEMA_VERSION}")
        if version < 1:
            self._db.execute("BEGIN EXCLUSIVE")
            try:
                self._db.execute("""CREATE TABLE residents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    energy INTEGER NOT NULL CHECK (energy BETWEEN 0 AND 100),
                    safety INTEGER NOT NULL CHECK (safety BETWEEN 0 AND 100),
                    growth INTEGER NOT NULL CHECK (growth BETWEEN 0 AND 100)
                )""")
                self._db.execute("PRAGMA user_version = 1")
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise
        if version < 2:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._db.execute("""CREATE TABLE conversation_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resident_id TEXT NOT NULL REFERENCES residents(id),
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    occurred_at TEXT NOT NULL
                )""")
                self._db.execute("CREATE INDEX conversation_resident_id ON conversation_messages (resident_id, id)")
                self._db.execute("PRAGMA user_version = 2")
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise

    def conversation(self, resident_id: str, limit: int = 12) -> list[dict[str, str]]:
        rows = self._db.execute(
            "SELECT role, content FROM conversation_messages WHERE resident_id = ? ORDER BY id DESC LIMIT ?",
            (resident_id, limit),
        ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    def record_exchange(self, resident_id: str, user_text: str, answer: str) -> WorldEvent:
        occurred_at = datetime.now(timezone.utc).isoformat()
        payload = {"message": answer}
        try:
            self._db.execute("BEGIN IMMEDIATE")
            self._db.executemany(
                "INSERT INTO conversation_messages (resident_id, role, content, occurred_at) VALUES (?, ?, ?, ?)",
                [(resident_id, "user", user_text, occurred_at),
                 (resident_id, "assistant", answer, occurred_at)],
            )
            cursor = self._db.execute(
                "INSERT INTO world_events (occurred_at, event_type, subject, payload_json) VALUES (?, ?, ?, ?)",
                (occurred_at, "resident.spoke", resident_id, json.dumps(payload, ensure_ascii=False)),
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return WorldEvent(cursor.lastrowid, occurred_at, "resident.spoke", resident_id, payload)

    def append(self, event_type: str, subject: str, payload: dict[str, object]) -> WorldEvent:
        occurred_at = datetime.now(timezone.utc).isoformat()
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        cursor = self._db.execute(
            "INSERT INTO world_events (occurred_at, event_type, subject, payload_json) VALUES (?, ?, ?, ?)",
            (occurred_at, event_type, subject, encoded),
        )
        self._db.commit()
        return WorldEvent(cursor.lastrowid, occurred_at, event_type, subject, payload)

    @staticmethod
    def _resident_values(resident: Resident) -> tuple[object, ...]:
        return (resident.id, resident.name, resident.energy, resident.safety, resident.growth)

    def create_resident(self, resident: Resident) -> WorldEvent:
        occurred_at = datetime.now(timezone.utc).isoformat()
        payload = {"name": resident.name}
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        try:
            self._db.execute("BEGIN IMMEDIATE")
            self._db.execute("INSERT INTO residents (id, name, energy, safety, growth) VALUES (?, ?, ?, ?, ?)",
                             self._resident_values(resident))
            cursor = self._db.execute(
                "INSERT INTO world_events (occurred_at, event_type, subject, payload_json) VALUES (?, ?, ?, ?)",
                (occurred_at, "resident.created", resident.id, encoded),
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return WorldEvent(cursor.lastrowid, occurred_at, "resident.created", resident.id, payload)

    def update_resident_and_append(self, resident: Resident, event_type: str,
                                   payload: dict[str, object]) -> WorldEvent:
        occurred_at = datetime.now(timezone.utc).isoformat()
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        try:
            self._db.execute("BEGIN IMMEDIATE")
            cursor = self._db.execute(
                "UPDATE residents SET name = ?, energy = ?, safety = ?, growth = ? WHERE id = ?",
                (resident.name, resident.energy, resident.safety, resident.growth, resident.id),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"unknown resident: {resident.id}")
            cursor = self._db.execute(
                "INSERT INTO world_events (occurred_at, event_type, subject, payload_json) VALUES (?, ?, ?, ?)",
                (occurred_at, event_type, resident.id, encoded),
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return WorldEvent(cursor.lastrowid, occurred_at, event_type, resident.id, payload)

    def get_resident(self, resident_id: str) -> Resident | None:
        row = self._db.execute(
            "SELECT id, name, energy, safety, growth FROM residents WHERE id = ?", (resident_id,)
        ).fetchone()
        return self._resident_from_row(row) if row else None

    def list_residents(self) -> list[Resident]:
        rows = self._db.execute(
            "SELECT id, name, energy, safety, growth FROM residents ORDER BY id"
        ).fetchall()
        return [self._resident_from_row(row) for row in rows]

    @staticmethod
    def _resident_from_row(row: sqlite3.Row) -> Resident:
        return Resident(row["id"], row["name"], row["energy"], row["safety"], row["growth"])

    def list_events(self, limit: int = 100) -> list[WorldEvent]:
        if not 1 <= limit <= 500:
            raise ValueError("event limit must be from 1 to 500")
        rows = self._db.execute(
            "SELECT id, occurred_at, event_type, subject, payload_json FROM world_events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        rows.reverse()
        return [WorldEvent(row["id"], row["occurred_at"], row["event_type"], row["subject"],
                           json.loads(row["payload_json"])) for row in rows]

    def close(self) -> None:
        self._db.close()
