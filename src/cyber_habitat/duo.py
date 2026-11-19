"""A separate, capability-protected room for two people."""
import argparse
import hashlib
import json
import secrets
import sqlite3
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


class Room(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port: int, db: Path):
        db.parent.mkdir(parents=True, exist_ok=True)
        self.db = db
        self.page = Path(__file__).with_name("duo.html").read_bytes()
        self.peers = {}
        with sqlite3.connect(db) as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS invites (
                seat INTEGER PRIMARY KEY CHECK (seat IN (1, 2)), token TEXT NOT NULL UNIQUE
            )""")
            for seat in (1, 2):
                connection.execute("INSERT OR IGNORE INTO invites VALUES (?, ?)",
                                   (seat, secrets.token_urlsafe(32)))
            connection.execute("""CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY, seat INTEGER NOT NULL, text TEXT NOT NULL,
                sent_at TEXT NOT NULL
            )""")
            self.invites = dict(connection.execute("SELECT seat, token FROM invites"))
        self.peers = {self.digest(token): seat for seat, token in self.invites.items()}
        super().__init__(("127.0.0.1", port), RoomHandler)

    @staticmethod
    def digest(token: str) -> bytes:
        return hashlib.sha256(token.encode("utf-8")).digest()


class RoomHandler(BaseHTTPRequestHandler):
    server: Room

    def setup(self):
        super().setup()
        self.connection.settimeout(8)

    def log_message(self, *args):
        pass

    def send_payload(self, status, data, content_type="application/json; charset=utf-8"):
        if isinstance(data, dict):
            data = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'unsafe-inline'; "
                         "style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(data)

    def seat(self):
        prefix, _, token = self.headers.get("Authorization", "").partition(" ")
        if prefix == "Bearer" and len(token) == 43:
            seat = self.server.peers.get(self.server.digest(token))
            if seat:
                return seat
        self.send_payload(HTTPStatus.UNAUTHORIZED, {"error": "邀请无效，请重新打开邀请链接。"})
        return None

    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path == "/":
            self.send_payload(200, self.server.page, "text/html; charset=utf-8")
            return
        if parsed.path != "/api/messages":
            self.send_payload(404, {"error": "地址不存在。"})
            return
        seat = self.seat()
        if seat is None:
            return
        try:
            after = int(parse_qs(parsed.query).get("after", ["0"])[0])
            if not 0 <= after < 2**63:
                raise ValueError
        except ValueError:
            self.send_payload(400, {"error": "消息游标无效。"})
            return
        with sqlite3.connect(self.server.db) as connection:
            connection.row_factory = sqlite3.Row
            if after:
                rows = connection.execute("SELECT * FROM messages WHERE id > ? ORDER BY id LIMIT 100", (after,))
                messages = [dict(row) for row in rows]
            else:
                rows = connection.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 100")
                messages = list(reversed([dict(row) for row in rows]))
        self.send_payload(200, {"seat": seat, "messages": messages})

    def do_POST(self):
        if self.path != "/api/messages":
            self.send_payload(404, {"error": "地址不存在。"})
            return
        seat = self.seat()
        if seat is None:
            return
        if self.headers.get_content_type() != "application/json":
            self.send_payload(415, {"error": "只接受 JSON。"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 8192:
                raise ValueError
            payload = json.loads(self.rfile.read(size))
            text = payload.get("text") if isinstance(payload, dict) else None
            if not isinstance(text, str) or not 1 <= len(text.strip()) <= 1000:
                raise ValueError
            text = text.strip()
            text.encode("utf-8")
        except (ValueError, TimeoutError):
            self.send_payload(400, {"error": "请输入 1 至 1000 字。"})
            return
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.server.db) as connection:
            message_id = connection.execute("INSERT INTO messages (seat, text, sent_at) VALUES (?, ?, ?)",
                                            (seat, text, now)).lastrowid
        self.send_payload(201, {"id": message_id})


def main():
    parser = argparse.ArgumentParser(description="Start a private two-person chat.")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--db", type=Path, default=Path("data/duo.sqlite3"))
    parser.add_argument("--origin", help="Optional private HTTPS origin for the invitation links")
    args = parser.parse_args()
    if args.origin:
        parsed = urlsplit(args.origin)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
                or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
            parser.error("--origin must be an HTTPS origin with no path, query or credentials")
    try:
        with Room(args.port, args.db) as room:
            local = f"http://127.0.0.1:{room.server_port}"
            print(f"Listening on {local}", flush=True)
            for seat, token in room.invites.items():
                print(f"Seat {seat}, local: {local}/#{token}", flush=True)
                if args.origin:
                    print(f"Seat {seat}, private link: {args.origin.rstrip('/')}/#{token}", flush=True)
            print("Treat the two links as passwords. Close this window to stop the room.", flush=True)
            room.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
