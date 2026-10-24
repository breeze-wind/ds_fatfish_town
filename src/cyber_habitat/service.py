from __future__ import annotations

import json
import re
import sqlite3
import uuid
from pathlib import Path
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from ipaddress import ip_address
from urllib.parse import parse_qs, urlsplit

from .director import WorldDirector
from .domain import Action, ActionKind, Resident
from .runtime import MockRuntime
from .store import SQLiteEventStore

MAX_BODY_BYTES = 16_384
RESIDENT_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _resident_json(resident: Resident) -> dict[str, object]:
    return {
        "id": resident.id,
        "name": resident.name,
        "energy": resident.energy,
        "safety": resident.safety,
        "growth": resident.growth,
    }


def _event_json(event) -> dict[str, object]:
    return {
        "id": event.id,
        "occurred_at": event.occurred_at,
        "type": event.event_type,
        "subject": event.subject,
        "payload": event.payload,
    }


class HabitatHTTPServer(HTTPServer):
    def __init__(self, address: tuple[str, int], db_path: str, seed: int,
                 random_event_chance: float):
        self.store = SQLiteEventStore(db_path)
        self.director = WorldDirector(
            MockRuntime(), self.store, seed=seed, random_event_chance=random_event_chance
        )
        try:
            super().__init__(address, HabitatRequestHandler)
        except Exception:
            self.store.close()
            raise

    def server_close(self) -> None:
        try:
            super().server_close()
        finally:
            self.store.close()


class HabitatRequestHandler(BaseHTTPRequestHandler):
    server: HabitatHTTPServer
    server_version = "CyberHabitat/0.2"
    sys_version = ""

    def log_message(self, format: str, *args: object) -> None:
        # Keep request bodies and resident names out of default access logs.
        return

    def _send(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: HTTPStatus, message: str) -> None:
        self._send(status, {"error": message})

    def _host_is_local(self) -> bool:
        host_header = self.headers.get("Host", "")
        try:
            hostname = urlsplit(f"//{host_header}").hostname
        except ValueError:
            return False
        if hostname is None:
            return False
        if hostname.lower() == "localhost":
            return True
        try:
            return ip_address(hostname).is_loopback
        except ValueError:
            return False

    def _read_json(self) -> dict[str, object] | None:
        content_type = self.headers.get_content_type()
        if content_type != "application/json":
            self._error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "Content-Type must be application/json")
            return None
        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length) if raw_length is not None else -1
        except ValueError:
            length = -1
        if not 0 <= length <= MAX_BODY_BYTES:
            self._error(HTTPStatus.BAD_REQUEST if length < 0 else HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        "invalid or oversized request body")
            return None
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._error(HTTPStatus.BAD_REQUEST, "request body must be valid UTF-8 JSON")
            return None
        if not isinstance(value, dict):
            self._error(HTTPStatus.BAD_REQUEST, "request body must be a JSON object")
            return None
        return value

    def do_GET(self) -> None:
        if not self._host_is_local():
            self._error(HTTPStatus.BAD_REQUEST, "Host must be localhost or a loopback address")
            return
        parsed = urlsplit(self.path)
        if parsed.path == "/":
            body = Path(__file__).with_name("habitat.html").read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path in ("/healthz", "/readyz"):
            self._send(HTTPStatus.OK, {"status": "ok"})
            return
        if parsed.path == "/residents":
            self._send(HTTPStatus.OK, {"residents": [
                _resident_json(resident) for resident in self.server.director.residents.values()
            ]})
            return
        if parsed.path.startswith("/residents/"):
            resident_id = parsed.path.removeprefix("/residents/")
            if not RESIDENT_ID.fullmatch(resident_id):
                self._error(HTTPStatus.NOT_FOUND, "resident not found")
                return
            resident = self.server.director.residents.get(resident_id)
            if resident is None:
                self._error(HTTPStatus.NOT_FOUND, "resident not found")
                return
            self._send(HTTPStatus.OK, {"resident": _resident_json(resident)})
            return
        if parsed.path == "/events":
            try:
                query = parse_qs(parsed.query, strict_parsing=True) if parsed.query else {}
            except ValueError:
                self._error(HTTPStatus.BAD_REQUEST, "invalid query string")
                return
            if set(query) - {"limit"} or any(len(items) != 1 for items in query.values()):
                self._error(HTTPStatus.BAD_REQUEST, "only one limit query parameter is supported")
                return
            try:
                limit = int(query.get("limit", ["100"])[0])
                events = self.server.store.list_events(limit)
            except (ValueError, TypeError):
                self._error(HTTPStatus.BAD_REQUEST, "limit must be an integer from 1 to 500")
                return
            self._send(HTTPStatus.OK, {"events": [_event_json(event) for event in events]})
            return
        self._error(HTTPStatus.NOT_FOUND, "route not found")

    def do_POST(self) -> None:
        if not self._host_is_local():
            self._error(HTTPStatus.BAD_REQUEST, "Host must be localhost or a loopback address")
            return
        parsed = urlsplit(self.path)
        body = self._read_json()
        if body is None:
            return
        if parsed.path == "/world/tick":
            if body:
                self._error(HTTPStatus.BAD_REQUEST, "tick body must be an empty object")
                return
            if not self.server.director.residents:
                self._error(HTTPStatus.CONFLICT, "create a resident before advancing the world")
                return
            events = self.server.director.tick()
            self._send(HTTPStatus.OK, {
                "residents": [_resident_json(resident) for resident in self.server.director.residents.values()],
                "events": [_event_json(event) for event in events],
            })
            return
        if parsed.path == "/residents":
            if set(body) - {"id", "name"} or not isinstance(body.get("name"), str):
                self._error(HTTPStatus.BAD_REQUEST, "body requires name and accepts optional id")
                return
            name = body["name"].strip()
            if not name or len(name) > 80:
                self._error(HTTPStatus.BAD_REQUEST, "name must contain 1 to 80 characters")
                return
            resident_id = body.get("id", uuid.uuid4().hex)
            if not isinstance(resident_id, str) or not RESIDENT_ID.fullmatch(resident_id):
                self._error(HTTPStatus.BAD_REQUEST, "id must use 1 to 64 letters, digits, '_' or '-'")
                return
            try:
                event = self.server.director.add_resident(Resident(resident_id, name))
            except (ValueError, sqlite3.IntegrityError):
                self._error(HTTPStatus.CONFLICT, "resident id already exists")
                return
            self._send(HTTPStatus.CREATED, {
                "resident": _resident_json(self.server.director.residents[resident_id]),
                "event": _event_json(event),
            })
            return

        action_prefix = "/residents/"
        action_suffix = "/actions"
        if parsed.path.startswith(action_prefix) and parsed.path.endswith(action_suffix):
            resident_id = parsed.path[len(action_prefix):-len(action_suffix)]
            if not RESIDENT_ID.fullmatch(resident_id):
                self._error(HTTPStatus.NOT_FOUND, "resident not found")
                return
            if set(body) - {"kind", "detail"} or not isinstance(body.get("kind"), str):
                self._error(HTTPStatus.BAD_REQUEST, "body requires kind and accepts optional detail")
                return
            detail = body.get("detail", "")
            if not isinstance(detail, str) or len(detail) > 240:
                self._error(HTTPStatus.BAD_REQUEST, "detail must be a string up to 240 characters")
                return
            try:
                kind = ActionKind(body["kind"])
            except ValueError:
                self._error(HTTPStatus.BAD_REQUEST, "kind must be rest, learn, socialize, or attack")
                return
            try:
                decision = self.server.director.submit(resident_id, Action(resident_id, kind, detail))
            except KeyError:
                self._error(HTTPStatus.NOT_FOUND, "resident not found")
                return
            self._send(HTTPStatus.OK, {
                "decision": {"allowed": decision.allowed, "reason": decision.reason},
                "resident": _resident_json(self.server.director.residents[resident_id]),
                "events": [_event_json(event) for event in decision.events],
            })
            return
        self._error(HTTPStatus.NOT_FOUND, "route not found")


def serve(host: str, port: int, db_path: str, *, seed: int = 0,
          random_event_chance: float = 0.15) -> None:
    if host not in {"0.0.0.0", "localhost"}:
        try:
            is_loopback = ip_address(host).is_loopback
        except ValueError as exc:
            raise ValueError("service host must be localhost, a loopback address, or 0.0.0.0") from exc
        if not is_loopback:
            raise ValueError("service may bind only to loopback or 0.0.0.0 inside a container")
    server = HabitatHTTPServer((host, port), db_path, seed, random_event_chance)
    print(f"Cyber Habitat listening on http://{host}:{port} (database: {db_path})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Cyber Habitat")
    finally:
        server.server_close()
