import json
import shutil
import sqlite3
import sys
import threading
import unittest
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cyber_habitat.service import HabitatHTTPServer
from cyber_habitat.store import SCHEMA_VERSION, SQLiteEventStore


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(__file__).resolve().parents[1] / "work" / uuid.uuid4().hex
        self.temp.mkdir(parents=True)
        self.db_path = self.temp / "world.sqlite3"
        self.server = None
        self.thread = None
        self._start_server()

    def tearDown(self):
        self._stop_server()
        shutil.rmtree(self.temp)

    def _start_server(self):
        self.server = HabitatHTTPServer(("127.0.0.1", 0), str(self.db_path), 7, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def _stop_server(self):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=2)
            self.server = None

    def request(self, method, path, payload=None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(self.base_url + path, data=data, method=method,
                          headers={"Content-Type": "application/json"} if data is not None else {})
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as error:
            response = error
        return response.code, json.loads(response.read().decode("utf-8"))

    def test_create_submit_block_and_restore_after_restart(self):
        status, created = self.request("POST", "/residents", {"id": "mori", "name": " Mori "})
        self.assertEqual(status, 201)
        self.assertEqual(created["resident"]["name"], "Mori")

        status, result = self.request("POST", "/residents/mori/actions", {"kind": "learn"})
        self.assertEqual(status, 200)
        self.assertTrue(result["decision"]["allowed"])
        self.assertEqual(result["resident"]["growth"], 32)
        self.assertEqual(result["resident"]["energy"], 60)

        status, result = self.request("POST", "/residents/mori/actions", {"kind": "attack"})
        self.assertEqual(status, 200)
        self.assertFalse(result["decision"]["allowed"])
        self.assertEqual(result["resident"]["growth"], 32)

        self._stop_server()
        self._start_server()
        status, result = self.request("GET", "/residents/mori")
        self.assertEqual(status, 200)
        self.assertEqual(result["resident"]["growth"], 32)
        status, result = self.request("GET", "/events?limit=20")
        self.assertEqual(status, 200)
        self.assertEqual([event["type"] for event in result["events"]], [
            "resident.created", "action.applied", "action.blocked"
        ])

    def test_health_and_input_validation(self):
        self.assertEqual(self.request("GET", "/healthz"), (200, {"status": "ok"}))
        self.assertEqual(self.request("GET", "/readyz"), (200, {"status": "ok"}))
        self.assertEqual(self.request("POST", "/residents", {"name": ""})[0], 400)
        self.request("POST", "/residents", {"id": "mori", "name": "Mori"})
        self.assertEqual(self.request("POST", "/residents", {"id": "mori", "name": "Again"})[0], 409)
        self.assertEqual(self.request("POST", "/residents/mori/actions", {"kind": "fly"})[0], 400)
        self.assertEqual(self.request("GET", "/events?limit=9999")[0], 400)
        self.assertEqual(self.request("GET", "/unknown")[0], 404)

        request = Request(self.base_url + "/healthz", headers={"Host": "attacker.example"})
        try:
            response = urlopen(request, timeout=3)
        except HTTPError as error:
            response = error
        self.assertEqual(response.code, 400)

    def test_browser_page_is_served(self):
        with urlopen(self.base_url + "/", timeout=3) as response:
            self.assertEqual(response.code, 200)
            self.assertIn("text/html", response.headers["Content-Type"])
            page = response.read().decode("utf-8")
            self.assertIn("让角色进场", page)
            self.assertIn("AI 推进一天", page)
            self.assertIn("chatResident", page)

    def test_tick_requires_resident_and_persists_result(self):
        self.assertEqual(self.request("POST", "/world/tick", {})[0], 409)
        self.request("POST", "/residents", {"id": "mori", "name": "Mori"})
        self.assertEqual(self.request("POST", "/world/tick", {"extra": 1})[0], 400)
        status, result = self.request("POST", "/world/tick", {})
        self.assertEqual(status, 200)
        self.assertEqual(result["residents"][0]["growth"], 32)
        self.assertEqual(result["events"][-1]["type"], "world.tick")
        self._stop_server()
        self._start_server()
        self.assertEqual(self.request("GET", "/residents/mori")[1]["resident"]["growth"], 32)

    def test_ai_conversation_and_proposal_are_persisted(self):
        class FakeModel:
            ready = True
            model = "fake"
            calls = []

            def complete(self, messages, *, json_mode=False):
                self.calls.append(messages)
                return '{"kind":"learn"}' if json_mode else "你好，我是 Mori。"

        model = FakeModel()
        self.server.model = model
        self.request("POST", "/residents", {"id": "mori", "name": "Mori"})
        status, answer = self.request("POST", "/residents/mori/conversation", {"message": "你好"})
        self.assertEqual(status, 200)
        self.assertEqual(answer["answer"], "你好，我是 Mori。")
        self.assertEqual(self.request("GET", "/residents/mori/conversation")[1]["messages"], [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好，我是 Mori。"},
        ])
        self.assertIn("你好", model.calls[0][-1]["content"])
        self.request("POST", "/residents/mori/conversation", {"message": "你还记得我吗"})
        self.assertIn("你好", model.calls[1][-2]["content"])
        self.assertEqual(self.request("POST", "/world/ai-tick", {})[0], 200)
        self.assertEqual(self.request("GET", "/residents/mori")[1]["resident"]["growth"], 32)
        self._stop_server()
        self._start_server()
        self.assertEqual(len(self.request("GET", "/residents/mori/conversation")[1]["messages"]), 4)

    def test_ai_harmful_proposal_is_blocked(self):
        self.server.model = type("BadModel", (), {
            "ready": True, "model": "fake", "complete": lambda _self, _messages, **_kwargs: '{"kind":"attack"}',
        })()
        self.request("POST", "/residents", {"id": "mori", "name": "Mori"})
        status, result = self.request("POST", "/world/ai-tick", {})
        self.assertEqual(status, 200)
        self.assertEqual(result["residents"][0]["growth"], 20)
        self.assertEqual(result["events"][0]["type"], "action.blocked")

    def test_ai_unconfigured_fails_without_recording_conversation(self):
        self.server.model = type("NoModel", (), {"ready": False, "model": ""})()
        self.request("POST", "/residents", {"id": "mori", "name": "Mori"})
        self.assertEqual(self.request("POST", "/residents/mori/conversation", {"message": "你好"})[0], 503)
        self.assertEqual(self.request("POST", "/world/ai-tick", {})[0], 503)
        self.assertEqual(self.request("GET", "/residents/mori/conversation")[1]["messages"], [])

    def test_deepseek_key_is_kept_in_memory_and_never_returned(self):
        self.server.model.api_key = ""
        self.assertFalse(self.request("GET", "/ai/status")[1]["configured"])
        status, result = self.request("POST", "/ai/connect", {"api_key": "test-only-secret"})
        self.assertEqual(status, 200)
        self.assertTrue(result["configured"])
        self.assertNotIn("test-only-secret", json.dumps(result))
        self.assertNotIn("test-only-secret", json.dumps(self.request("GET", "/ai/status")[1]))
        self.assertEqual(self.request("POST", "/ai/disconnect", {})[1], {"configured": False})
        self.assertFalse(self.request("GET", "/ai/status")[1]["configured"])

    def test_legacy_event_database_migrates_in_place(self):
        self._stop_server()
        legacy_path = self.temp / "legacy.sqlite3"
        connection = sqlite3.connect(legacy_path)
        connection.execute("""CREATE TABLE world_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurred_at TEXT NOT NULL,
            event_type TEXT NOT NULL,
            subject TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )""")
        connection.commit()
        connection.close()

        store = SQLiteEventStore(legacy_path)
        try:
            version = store._db.execute("PRAGMA user_version").fetchone()[0]
            self.assertEqual(version, SCHEMA_VERSION)
            self.assertEqual(store.list_residents(), [])
        finally:
            store.close()


if __name__ == "__main__":
    unittest.main()
