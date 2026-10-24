import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cyber_habitat.ai import ModelUnavailable, OpenAICompatibleModel


class ModelTests(unittest.TestCase):
    def test_configuration_rejects_insecure_remote_url(self):
        with self.assertRaises(ValueError):
            OpenAICompatibleModel("http://example.com/v1", "model", "key")
        with self.assertRaises(ValueError):
            OpenAICompatibleModel("https://user:password@example.com/v1", "model", "key")
        self.assertFalse(OpenAICompatibleModel().ready)

    def test_local_chat_completions_request(self):
        captured = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                captured["path"] = self.path
                captured["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                body = json.dumps({"choices": [{"message": {"content": "你好，我是 Mori。"}}]}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            model = OpenAICompatibleModel(f"http://127.0.0.1:{server.server_port}/v1", "local")
            self.assertTrue(model.ready)
            self.assertEqual(model.complete([{"role": "user", "content": "你好"}]), "你好，我是 Mori。")
            self.assertEqual(captured["path"], "/v1/chat/completions")
            self.assertEqual(captured["body"]["model"], "local")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
