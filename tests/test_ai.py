import json
import sys
import threading
import tempfile
import unittest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cyber_habitat.ai import ModelUnavailable, OpenAICompatibleModel


class ModelTests(unittest.TestCase):
    def test_deepseek_payload_is_explicit_and_json_mode_is_supported(self):
        captured = {}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _limit):
                return b'{"choices":[{"message":{"content":"{\\"kind\\":\\"learn\\"}"}}]}'

        class Opener:
            def open(self, request, timeout):
                captured["url"] = request.full_url
                captured["body"] = json.loads(request.data)
                captured["timeout"] = timeout
                return Response()

        with patch("cyber_habitat.ai.build_opener", return_value=Opener()):
            model = OpenAICompatibleModel("https://api.deepseek.com", "deepseek-flash", "test-only")
            self.assertEqual(model.complete([{"role": "user", "content": "choose"}], json_mode=True),
                             '{"kind":"learn"}')
        self.assertEqual(captured["url"], "https://api.deepseek.com/chat/completions")
        self.assertEqual(captured["body"]["thinking"], {"type": "disabled"})
        self.assertEqual(captured["body"]["response_format"], {"type": "json_object"})

    def test_configuration_rejects_insecure_remote_url(self):
        with self.assertRaises(ValueError):
            OpenAICompatibleModel("http://example.com/v1", "model", "key")
        with self.assertRaises(ValueError):
            OpenAICompatibleModel("https://user:password@example.com/v1", "model", "key")
        default = OpenAICompatibleModel(api_key="")
        self.assertEqual(default.base_url, "https://api.deepseek.com")
        self.assertEqual(default.model, "deepseek-flash")
        self.assertFalse(default.ready)

    def test_local_config_key_is_loaded_and_can_be_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            model = OpenAICompatibleModel(api_key="", config_path=path)
            model.remember_api_key("test-key-only")
            self.assertIn("HABITAT_AI_API_KEY=test-key-only", path.read_text(encoding="utf-8"))
            reloaded = OpenAICompatibleModel(config_path=path)
            self.assertEqual(reloaded.api_key, "test-key-only")
            self.assertEqual(reloaded.key_source, "local_config")
            reloaded.forget_saved_key()
            self.assertNotIn("HABITAT_AI_API_KEY=", path.read_text(encoding="utf-8"))

    def test_environment_config_path_persists_key_for_container_volume(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data" / ".env"
            with patch.dict("os.environ", {"HABITAT_AI_CONFIG_PATH": str(path)}):
                model = OpenAICompatibleModel(api_key="")
                model.remember_api_key("volume-key-only")
                reloaded = OpenAICompatibleModel()
            self.assertEqual(reloaded.api_key, "volume-key-only")
            self.assertTrue(path.exists())
            reloaded.forget_saved_key()
            self.assertNotIn("HABITAT_AI_API_KEY=", path.read_text(encoding="utf-8"))

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
