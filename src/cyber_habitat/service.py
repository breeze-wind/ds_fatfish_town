from __future__ import annotations

import json
import re
import sqlite3
import uuid
from pathlib import Path
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from ipaddress import ip_address
from urllib.request import Request, urlopen
from urllib.parse import parse_qs, urlsplit

from .director import WorldDirector
from .ai import ModelUnavailable, OpenAICompatibleModel, action_prompt, conversation_prompt
from .autonomy import AutonomousLife
from .domain import Action, ActionKind, Resident
from .onebot import OneBotBridge
from .runtime import MockRuntime
from .store import SQLiteEventStore

MAX_BODY_BYTES = 16_384
RESIDENT_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _resident_json(resident: Resident, intention: str | None = None) -> dict[str, object]:
    return {
        "id": resident.id,
        "name": resident.name,
        "energy": resident.energy,
        "safety": resident.safety,
        "growth": resident.growth,
        "intention": intention,
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
        self.model = OpenAICompatibleModel()
        self.onebot = OneBotBridge()
        try:
            super().__init__(address, HabitatRequestHandler)
            self.autonomy = AutonomousLife(self._autonomous_step)
        except Exception:
            self.store.close()
            raise

    def _autonomous_step(self, resident_id: str) -> None:
        # The single-threaded HTTP server serializes SQLite access and model calls.
        url = f"http://127.0.0.1:{self.server_port}/world/ai-tick"
        request = Request(url, data=json.dumps({"resident_id": resident_id}).encode("utf-8"),
                          headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=90) as response:
            response.read()

    def respond_to_resident(self, resident_id: str, message: str):
        if not self.model.ready:
            raise ModelUnavailable("AI model is not configured")
        resident = self.director.residents[resident_id]
        prompt = conversation_prompt(resident.name,
                                     {"energy": resident.energy, "safety": resident.safety,
                                      "growth": resident.growth},
                                     self.store.conversation(resident_id), message)
        answer = self.model.complete(prompt)
        return answer, self.store.record_exchange(resident_id, message, answer)

    def server_close(self) -> None:
        try:
            self.autonomy.close()
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
        if parsed.path == "/ai/status":
            self._send(HTTPStatus.OK, {"configured": self.server.model.ready,
                                       "model": self.server.model.model if self.server.model.ready else None,
                                       "key_source": self.server.model.key_source})
            return
        if parsed.path == "/autonomy":
            self._send(HTTPStatus.OK, self.server.autonomy.status())
            return
        if parsed.path == "/integrations/onebot/status":
            self._send(HTTPStatus.OK, {"configured": self.server.onebot.configured,
                                       "resident_id": self.server.onebot.resident_id or None})
            return
        if parsed.path == "/residents":
            self._send(HTTPStatus.OK, {"residents": [
                _resident_json(resident, self.server.store.get_intention(resident.id))
                for resident in self.server.director.residents.values()
            ]})
            return
        if parsed.path.startswith("/residents/"):
            resident_id = parsed.path.removeprefix("/residents/")
            if resident_id.endswith("/conversation"):
                resident_id = resident_id.removesuffix("/conversation")
                if not RESIDENT_ID.fullmatch(resident_id) or resident_id not in self.server.director.residents:
                    self._error(HTTPStatus.NOT_FOUND, "resident not found")
                    return
                self._send(HTTPStatus.OK, {"messages": self.server.store.conversation(resident_id, 30)})
                return
            if not RESIDENT_ID.fullmatch(resident_id):
                self._error(HTTPStatus.NOT_FOUND, "resident not found")
                return
            resident = self.server.director.residents.get(resident_id)
            if resident is None:
                self._error(HTTPStatus.NOT_FOUND, "resident not found")
                return
            self._send(HTTPStatus.OK, {"resident": _resident_json(resident, self.server.store.get_intention(resident.id))})
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
        if parsed.path == "/ai/connect":
            origin = self.headers.get("Origin")
            if origin and origin != f"http://{self.headers.get('Host', '')}":
                self._error(HTTPStatus.FORBIDDEN, "cross-origin key entry is not allowed")
                return
            if self.server.model.base_url != "https://api.deepseek.com":
                self._error(HTTPStatus.CONFLICT, "browser key entry supports only the official DeepSeek URL")
                return
            if set(body) - {"api_key", "remember"} or not isinstance(body.get("api_key"), str):
                self._error(HTTPStatus.BAD_REQUEST, "body requires api_key and accepts remember")
                return
            remember = body.get("remember", False)
            if type(remember) is not bool:
                self._error(HTTPStatus.BAD_REQUEST, "remember must be a boolean")
                return
            key = body["api_key"].strip()
            if not 1 <= len(key) <= 512 or any(char.isspace() for char in key):
                self._error(HTTPStatus.BAD_REQUEST, "invalid API key")
                return
            if remember:
                self.server.model.remember_api_key(key)
            else:
                self.server.model.api_key = key
                self.server.model.key_source = "memory"
            self._send(HTTPStatus.OK, {"configured": True, "model": self.server.model.model,
                                       "key_source": self.server.model.key_source})
            return
        if parsed.path == "/integrations/onebot/events":
            text = self.server.onebot.accepts(self.headers.get("Authorization"), body)
            if text is None:
                self._error(HTTPStatus.UNAUTHORIZED, "invalid or unsupported OneBot event")
                return
            resident_id = self.server.onebot.resident_id
            if not resident_id and len(self.server.director.residents) == 1:
                resident_id = next(iter(self.server.director.residents))
            if not resident_id or resident_id not in self.server.director.residents:
                self._error(HTTPStatus.CONFLICT, "OneBot resident is not configured")
                return
            try:
                answer, event = self.server.respond_to_resident(resident_id, text)
                self.server.onebot.send_private(answer)
            except ModelUnavailable as exc:
                self._error(HTTPStatus.BAD_GATEWAY, str(exc))
                return
            except (OSError, RuntimeError) as exc:
                self._error(HTTPStatus.BAD_GATEWAY, f"OneBot reply failed: {type(exc).__name__}")
                return
            self._send(HTTPStatus.OK, {"event": _event_json(event)})
            return
        if parsed.path == "/ai/disconnect":
            if set(body) - {"forget"}:
                self._error(HTTPStatus.BAD_REQUEST, "disconnect accepts only forget")
                return
            forget = body.get("forget", False)
            if type(forget) is not bool:
                self._error(HTTPStatus.BAD_REQUEST, "forget must be a boolean")
                return
            self.server.model.api_key = ""
            self.server.model.key_source = "none"
            if forget:
                self.server.model.forget_saved_key()
            self.server.autonomy.configure(None, enabled=False)
            self._send(HTTPStatus.OK, {"configured": False, "saved_key_removed": forget})
            return
        if parsed.path == "/autonomy":
            if set(body) - {"enabled", "resident_id", "interval_seconds", "max_calls_per_day"} or type(body.get("enabled")) is not bool:
                self._error(HTTPStatus.BAD_REQUEST, "body requires enabled and accepts resident_id, interval_seconds, max_calls_per_day")
                return
            enabled = body["enabled"]
            resident_id = body.get("resident_id")
            if enabled and (not isinstance(resident_id, str) or resident_id not in self.server.director.residents):
                self._error(HTTPStatus.NOT_FOUND, "resident not found")
                return
            if enabled and not self.server.model.ready:
                self._error(HTTPStatus.SERVICE_UNAVAILABLE, "AI model is not configured")
                return
            interval = body.get("interval_seconds", 1800)
            maximum = body.get("max_calls_per_day", 24)
            if type(interval) is not int or type(maximum) is not int:
                self._error(HTTPStatus.BAD_REQUEST, "interval and daily cap must be integers")
                return
            try:
                status = self.server.autonomy.configure(resident_id, enabled=enabled,
                                                         interval_seconds=interval, max_calls_per_day=maximum)
            except ValueError as exc:
                self._error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self._send(HTTPStatus.OK, status)
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
                "residents": [_resident_json(resident, self.server.store.get_intention(resident.id))
                              for resident in self.server.director.residents.values()],
                "events": [_event_json(event) for event in events],
            })
            return
        if parsed.path == "/world/ai-tick":
            if set(body) - {"resident_id"}:
                self._error(HTTPStatus.BAD_REQUEST, "AI tick accepts only resident_id")
                return
            if not self.server.model.ready:
                self._error(HTTPStatus.SERVICE_UNAVAILABLE, "AI model is not configured")
                return
            if not self.server.director.residents:
                self._error(HTTPStatus.CONFLICT, "create a resident before advancing the world")
                return
            target = body.get("resident_id")
            if target is not None and (not isinstance(target, str) or target not in self.server.director.residents):
                self._error(HTTPStatus.NOT_FOUND, "resident not found")
                return
            events = []
            for resident_id in ([target] if target else sorted(self.server.director.residents)):
                resident = self.server.director.residents[resident_id]
                recent_events = [{"type": event.event_type, "subject": event.subject,
                                  "payload": event.payload} for event in self.server.store.list_events(30)
                                 if event.subject in {"world", resident_id} and event.event_type != "resident.spoke"]
                prompt = action_prompt(resident.name, {"energy": resident.energy,
                                       "safety": resident.safety, "growth": resident.growth},
                                       self.server.store.get_intention(resident_id),
                                       self.server.store.conversation(resident_id, 6), recent_events)
                try:
                    raw = self.server.model.complete(prompt, json_mode=True)
                    proposal = json.loads(raw)
                    kind = ActionKind(proposal["kind"])
                    reason = proposal["reason"]
                    intention = proposal["intention"]
                    if (set(proposal) != {"kind", "reason", "intention"} or not isinstance(reason, str)
                            or not isinstance(intention, str) or not 1 <= len(reason.strip()) <= 140
                            or not 1 <= len(intention.strip()) <= 160):
                        raise ValueError("unexpected proposal fields")
                except ModelUnavailable as exc:
                    self._error(HTTPStatus.BAD_GATEWAY, str(exc))
                    return
                except (ValueError, KeyError, TypeError):
                    events.append(self.server.store.append("ai.proposal.rejected", resident_id,
                                                           {"reason": "invalid action proposal"}))
                    continue
                events.append(self.server.store.set_intention(resident_id, intention.strip()))
                decision = self.server.director.submit(resident_id, Action(resident_id, kind, reason.strip()))
                events.extend(decision.events)
            events.append(self.server.store.append("world.ai_tick", "world", {"residents": len([target] if target else self.server.director.residents)}))
            self._send(HTTPStatus.OK, {"residents": [_resident_json(r, self.server.store.get_intention(r.id)) for r in self.server.director.residents.values()],
                                       "events": [_event_json(event) for event in events]})
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
                "resident": _resident_json(self.server.director.residents[resident_id], self.server.store.get_intention(resident_id)),
                "event": _event_json(event),
            })
            return

        conversation_suffix = "/conversation"
        if parsed.path.startswith("/residents/") and parsed.path.endswith(conversation_suffix):
            resident_id = parsed.path[len("/residents/"):-len(conversation_suffix)]
            if not RESIDENT_ID.fullmatch(resident_id) or resident_id not in self.server.director.residents:
                self._error(HTTPStatus.NOT_FOUND, "resident not found")
                return
            if set(body) != {"message"} or not isinstance(body.get("message"), str):
                self._error(HTTPStatus.BAD_REQUEST, "body requires message")
                return
            message = body["message"].strip()
            if not 1 <= len(message) <= 1000:
                self._error(HTTPStatus.BAD_REQUEST, "message must contain 1 to 1000 characters")
                return
            if not self.server.model.ready:
                self._error(HTTPStatus.SERVICE_UNAVAILABLE, "AI model is not configured")
                return
            try:
                answer, event = self.server.respond_to_resident(resident_id, message)
            except ModelUnavailable as exc:
                self._error(HTTPStatus.BAD_GATEWAY, str(exc))
                return
            self._send(HTTPStatus.OK, {"answer": answer, "event": _event_json(event)})
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
                self._error(HTTPStatus.BAD_REQUEST, "kind must be rest, learn, socialize, explore, create, or attack")
                return
            try:
                decision = self.server.director.submit(resident_id, Action(resident_id, kind, detail))
            except KeyError:
                self._error(HTTPStatus.NOT_FOUND, "resident not found")
                return
            self._send(HTTPStatus.OK, {
                "decision": {"allowed": decision.allowed, "reason": decision.reason},
                "resident": _resident_json(self.server.director.residents[resident_id], self.server.store.get_intention(resident_id)),
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
