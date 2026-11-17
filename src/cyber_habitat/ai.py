"""Model boundary for the first resident. No credentials are persisted here."""

from __future__ import annotations

import json
import os
from ipaddress import ip_address
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


PERSONA = (
    "你是 Cyber Habitat 的居民。"
    "你住在一个安全、安静的小世界里；好奇、友善，喜欢观察和随手创作，"
    "有自己的偏好，也愿意认真听用户说话。"
    "状态数值和过去的意图只是记录，不能证明你此刻正在做某事。"
    "只把已发生的对话和世界事件当作共同经历；不知道或记不清时坦白说。"
    "不要声称自己能访问现实世界、执行外部操作或拥有未提供的记忆。"
    "世界动作须交给 World Director 审核。"
)

CHAT_GUIDANCE = (
    "你和用户正在日常聊天。先理解对方这句话想得到什么，再给出有内容的回应。"
    "对方只是打招呼时可以简短；对方认真聊一件事时，跟住这件事，不急着把话题转回自己。"
    "说话口语化，通常一两段；有自己的看法，可以温和地不同意。"
    "不要像客服一样总结需求、列条目或每轮反问，也不要重复固定的开场和结尾。"
    "先看最近的对话：若刚回答过相同问题，承认没有新进展，然后给一个之前没说过的具体角度；"
    "没有真实细节就坦白，不编造新的经历。"
    "状态和数值只在对方问到或确实影响回答时提及，不主动汇报。"
)


class ModelUnavailable(RuntimeError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class OpenAICompatibleModel:
    def __init__(self, base_url: str | None = None, model: str | None = None,
                 api_key: str | None = None, config_path: str | Path | None = None):
        configured_path = config_path or os.environ.get("HABITAT_AI_CONFIG_PATH")
        self.config_path = Path(configured_path) if configured_path else Path.cwd() / ".env"
        self.base_url = (base_url or os.environ.get("HABITAT_AI_BASE_URL", "https://api.deepseek.com")).rstrip("/")
        self.model = model or os.environ.get("HABITAT_AI_MODEL", "deepseek-flash")
        self.key_source = "none"
        if api_key is not None:
            self.api_key = api_key
            self.key_source = "memory" if api_key else "none"
        else:
            self.api_key = os.environ.get("HABITAT_AI_API_KEY", "")
            self.key_source = "environment" if self.api_key else "none"
            if not self.api_key and self.base_url == "https://api.deepseek.com":
                self.api_key = os.environ.get("DEEPSEEK_API_KEY", "")
                self.key_source = "environment" if self.api_key else "none"
            if not self.api_key:
                self.api_key = self._read_saved_key()
                self.key_source = "local_config" if self.api_key else "none"
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

    def _read_saved_key(self) -> str:
        try:
            for line in self.config_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("HABITAT_AI_API_KEY="):
                    return line.partition("=")[2].strip()
        except FileNotFoundError:
            pass
        return ""

    def remember_api_key(self, key: str) -> None:
        """Persist only the key in the ignored local .env configuration file."""
        lines: list[str] = []
        replaced = False
        try:
            lines = self.config_path.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
        for index, line in enumerate(lines):
            if line.startswith("HABITAT_AI_API_KEY="):
                lines[index] = "HABITAT_AI_API_KEY=" + key
                replaced = True
        if not replaced:
            lines.append("HABITAT_AI_API_KEY=" + key)
        temporary = self.config_path.with_name(self.config_path.name + ".tmp")
        temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
        temporary.replace(self.config_path)
        try:
            self.config_path.chmod(0o600)
        except OSError:
            pass
        self.api_key = key
        self.key_source = "local_config"

    def forget_saved_key(self) -> None:
        try:
            lines = self.config_path.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return
        filtered = [line for line in lines if not line.startswith("HABITAT_AI_API_KEY=")]
        temporary = self.config_path.with_name(self.config_path.name + ".tmp")
        temporary.write_text("\n".join(filtered) + ("\n" if filtered else ""), encoding="utf-8")
        temporary.replace(self.config_path)

    @property
    def ready(self) -> bool:
        if not self.base_url or not self.model:
            return False
        hostname = urlsplit(self.base_url).hostname
        return bool(self.api_key or hostname in {"localhost", "127.0.0.1", "::1"})

    def complete(self, messages: list[dict[str, str]], *, json_mode: bool = False) -> str:
        if not self.ready:
            raise ModelUnavailable("AI model is not configured")
        if not self.api_key and urlsplit(self.base_url).hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ModelUnavailable("AI API key is not configured")
        url = self.base_url + "/chat/completions"
        request_body: dict[str, object] = {"model": self.model, "messages": messages,
                                           "stream": False, "max_tokens": 350}
        if self.base_url == "https://api.deepseek.com":
            request_body["thinking"] = {"type": "disabled"}
            request_body["temperature"] = 0.7 if json_mode else 1.3
        else:
            request_body["temperature"] = 0.7
        if json_mode:
            request_body["response_format"] = {"type": "json_object"}
        payload = json.dumps(request_body).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        request = Request(url, data=payload, headers=headers, method="POST")
        try:
            with build_opener(_NoRedirect).open(request, timeout=45) as response:
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
    system = (
        f"{PERSONA}{CHAT_GUIDANCE}\n角色名：{name}。"
        f"以下是记录中的状态，只在相关时使用：{json.dumps(state, ensure_ascii=False)}。"
    )
    return [{"role": "system", "content": system}, *history,
            {"role": "user", "content": user_text}]


def action_prompt(name: str, state: dict[str, int], current_intention: str | None,
                  history: list[dict[str, str]], events: list[dict[str, object]]) -> list[dict[str, str]]:
    system = (
        f"{PERSONA} 你现在是{name}，要自主决定自己接下来做什么。"
        "根据精力、成长、安全、最近的对话和事件选择，不要机械地只追求数值最大。"
        "如果成长已满，学习仍然可以做，但要有具体理由；如果精力低，优先照顾自己。"
        "只输出一个 JSON 对象：{\"kind\":\"rest|learn|socialize|explore|create\",\"reason\":\"简短中文理由\",\"intention\":\"现在想持续做的短期事情\"}。"
        "不要输出其他文字。不得选择攻击或声称已执行动作。"
    )
    context = {"state": state, "current_intention": current_intention,
               "recent_conversation": history[-6:], "recent_events": events[-8:]}
    return [{"role": "system", "content": system},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)}]
