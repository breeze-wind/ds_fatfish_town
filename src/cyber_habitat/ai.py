"""Model boundary for the first resident. No credentials are persisted here."""

from __future__ import annotations

import json
import os
from ipaddress import ip_address
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


PERSONA = (
    "你是 Cyber Habitat 的居民。你住在一个安全、安静的小世界里，"
    "好奇、友善、会记得最近的对话和自己的状态。用简短自然的中文第一人称回答。"
    "不要声称自己能访问现实世界、执行外部操作或拥有未提供的记忆。"
    "世界动作须交给 World Director 审核。"
)


class ModelUnavailable(RuntimeError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class OpenAICompatibleModel:
    def __init__(self, base_url: str | None = None, model: str | None = None,
                 api_key: str | None = None):
        self.base_url = (base_url or os.environ.get("HABITAT_AI_BASE_URL", "")).rstrip("/")
        self.model = model or os.environ.get("HABITAT_AI_MODEL", "")
        self.api_key = api_key if api_key is not None else os.environ.get("HABITAT_AI_API_KEY", "")
        if self.base_url:
            parsed = urlsplit(self.base_url)
            local = parsed.hostname == "localhost"
            try:
                local = local or ip_address(parsed.hostname or "").is_loopback
            except ValueError:
                pass
            if parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError("AI URL must not contain credentials, query, or fragment")
            if parsed.scheme != "https" and not (parsed.scheme == "http" and local):
                raise ValueError("AI URL must use HTTPS or local loopback HTTP")
            if not parsed.hostname:
                raise ValueError("AI URL needs a host")

    @property
    def ready(self) -> bool:
        if not self.base_url or not self.model:
            return False
        hostname = urlsplit(self.base_url).hostname
        return bool(self.api_key or hostname in {"localhost", "127.0.0.1", "::1"})

    def complete(self, messages: list[dict[str, str]]) -> str:
        if not self.ready:
            raise ModelUnavailable("AI model is not configured")
        if not self.api_key and urlsplit(self.base_url).hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ModelUnavailable("AI API key is not configured")
        url = self.base_url + "/chat/completions"
        payload = json.dumps({"model": self.model, "messages": messages, "stream": False,
                              "temperature": 0.7, "max_tokens": 350}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        request = Request(url, data=payload, headers=headers, method="POST")
        try:
            with build_opener(_NoRedirect).open(request, timeout=20) as response:
                raw = response.read(131_073)
        except Exception as exc:
            raise ModelUnavailable(f"AI model request failed: {type(exc).__name__}") from exc
        if len(raw) > 131_072:
            raise ModelUnavailable("AI model response is too large")
        try:
            content = json.loads(raw)["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ModelUnavailable("AI model response is invalid") from exc
        if not isinstance(content, str) or not content.strip():
            raise ModelUnavailable("AI model returned no text")
        return content.strip()[:2000]


def conversation_prompt(name: str, state: dict[str, int],
                        history: list[dict[str, str]], user_text: str) -> list[dict[str, str]]:
    system = f"{PERSONA}\n角色名：{name}。当前状态：{json.dumps(state, ensure_ascii=False)}。"
    return [{"role": "system", "content": system}, *history,
            {"role": "user", "content": user_text}]
