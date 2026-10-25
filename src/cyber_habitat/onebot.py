"""Optional local OneBot v11 bridge for QQ private-message interaction."""

from __future__ import annotations

import json
import os
import re
from ipaddress import ip_address
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def _config_value(name: str) -> str:
    value = os.environ.get(name, "")
    if value:
        return value
    try:
        with open(".env", encoding="utf-8") as config:
            for line in config:
                if line.startswith(name + "="):
                    return line.partition("=")[2].strip()
    except FileNotFoundError:
        pass
    return ""


def trusted_internal_hosts() -> set[str]:
    """Explicit Compose service names permitted for private container traffic."""
    return {
        host.strip().lower().rstrip(".")
        for host in _config_value("HABITAT_TRUSTED_INTERNAL_HOSTS").split(",")
        if host.strip()
    }


class OneBotBridge:
    def __init__(self, url: str | None = None, access_token: str | None = None,
                 target_user_id: str | None = None, inbound_token: str | None = None):
        self.url = (url if url is not None else _config_value("HABITAT_ONEBOT_URL")).rstrip("/")
        self.access_token = access_token if access_token is not None else _config_value("HABITAT_ONEBOT_ACCESS_TOKEN")
        self.target_user_id = target_user_id if target_user_id is not None else _config_value("HABITAT_ONEBOT_TARGET_USER_ID")
        self.inbound_token = inbound_token if inbound_token is not None else _config_value("HABITAT_ONEBOT_INBOUND_TOKEN")
        self.resident_id = _config_value("HABITAT_ONEBOT_RESIDENT_ID")
        if self.url:
            parsed = urlsplit(self.url)
            hostname = (parsed.hostname or "").lower().rstrip(".")
            try:
                local = hostname == "localhost" or ip_address(hostname).is_loopback
            except ValueError:
                local = False
            internal = hostname in trusted_internal_hosts()
            if (parsed.scheme != "http" or not (local or internal) or parsed.username or parsed.password
                    or parsed.query or parsed.fragment or parsed.path not in ("", "/")):
                raise ValueError("OneBot URL must use loopback HTTP or an explicitly trusted internal host")

    @property
    def configured(self) -> bool:
        return bool(self.url and self.access_token and self.target_user_id.isdecimal() and self.inbound_token)

    def accepts(self, authorization: str | None, event: dict[str, object]) -> str | None:
        if not self.configured:
            return None
        if authorization != "Bearer " + self.inbound_token:
            return None
        if event.get("post_type") != "message" or event.get("message_type") != "private":
            return None
        sender = str(event.get("user_id", ""))
        if sender != self.target_user_id:
            return None
        text = event.get("raw_message")
        if not isinstance(text, str):
            return None
        text = re.sub(r"\[CQ:[^\]]+\]", "", text).strip()
        return text if 1 <= len(text) <= 1000 else None

    def send_private(self, text: str) -> None:
        if not self.configured:
            return
        payload = json.dumps({"user_id": int(self.target_user_id), "message": text[:2000]}).encode("utf-8")
        request = Request(self.url + "/send_private_msg", data=payload, method="POST",
                          headers={"Content-Type": "application/json", "Authorization": "Bearer " + self.access_token})
        with urlopen(request, timeout=15) as response:
            if not 200 <= response.status < 300:
                raise RuntimeError("OneBot send failed")
