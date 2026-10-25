import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cyber_habitat.onebot import OneBotBridge


class OneBotTests(unittest.TestCase):
    def test_accepts_only_configured_authorized_target_private_text(self):
        bridge = OneBotBridge("http://127.0.0.1:5700", "outbound", "123", "inbound")
        event = {"post_type": "message", "message_type": "private", "user_id": 123,
                 "raw_message": "你好 [CQ:face,id=14]"}
        self.assertEqual(bridge.accepts("Bearer inbound", event), "你好")
        self.assertIsNone(bridge.accepts("Bearer wrong", event))
        self.assertIsNone(bridge.accepts("Bearer inbound", {**event, "user_id": 456}))
        self.assertIsNone(bridge.accepts("Bearer inbound", {**event, "message_type": "group"}))

    def test_sends_only_to_loopback_onebot_endpoint(self):
        captured = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                captured["path"] = self.path
                captured["authorization"] = self.headers["Authorization"]
                captured["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                self.send_response(200)
                self.end_headers()

            def log_message(self, *_args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            bridge = OneBotBridge(f"http://127.0.0.1:{server.server_port}", "outbound", "123", "inbound")
            bridge.send_private("Mori 的回复")
            self.assertEqual(captured["path"], "/send_private_msg")
            self.assertEqual(captured["authorization"], "Bearer outbound")
            self.assertEqual(captured["body"], {"user_id": 123, "message": "Mori 的回复"})
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_docker_service_name_requires_explicit_trust(self):
        with patch.dict("os.environ", {"HABITAT_TRUSTED_INTERNAL_HOSTS": "napcat,cyber-habitat"}):
            bridge = OneBotBridge("http://napcat:5700", "outbound", "123", "inbound")
        self.assertEqual(bridge.url, "http://napcat:5700")
        with patch.dict("os.environ", {"HABITAT_TRUSTED_INTERNAL_HOSTS": "napcat,cyber-habitat"}):
            with self.assertRaises(ValueError):
                OneBotBridge("http://other-service:5700", "outbound", "123", "inbound")


if __name__ == "__main__":
    unittest.main()
