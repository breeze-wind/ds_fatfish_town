from typing import Protocol

from .domain import Action, Resident


class RuntimePort(Protocol):
    def apply(self, resident: Resident, action: Action) -> Resident: ...


class EventStorePort(Protocol):
    def append(self, event_type: str, subject: str, payload: dict[str, object]): ...
