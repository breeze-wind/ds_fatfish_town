from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ActionKind(StrEnum):
    REST = "rest"
    LEARN = "learn"
    SOCIALIZE = "socialize"
    EXPLORE = "explore"
    CREATE = "create"
    ATTACK = "attack"


@dataclass(frozen=True)
class Action:
    resident_id: str
    kind: ActionKind
    detail: str = ""


@dataclass(frozen=True)
class Resident:
    id: str
    name: str
    energy: int = 70
    safety: int = 70
    growth: int = 20

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.name.strip():
            raise ValueError("resident id and name must be non-empty")
        for key in ("energy", "safety", "growth"):
            value = getattr(self, key)
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
                raise ValueError(f"{key} must be an integer from 0 to 100")


@dataclass(frozen=True)
class WorldEvent:
    id: int
    occurred_at: str
    event_type: str
    subject: str
    payload: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    events: tuple[WorldEvent, ...]
