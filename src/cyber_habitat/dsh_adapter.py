"""Optional integration seam. No DSH vendor API is assumed in Sprint 0."""

from typing import Protocol

from .domain import Action, Resident


class DSHClient(Protocol):
    """A future, verified client wrapper supplied by the chosen DSH product."""
    def apply_resident_action(self, resident_id: str, action: str) -> dict[str, int]: ...


class DSHRuntimeAdapter:
    def __init__(self, client: DSHClient):
        self.client = client

    def apply(self, resident: Resident, action: Action) -> Resident:
        state = self.client.apply_resident_action(resident.id, action.kind.value)
        return Resident(id=resident.id, name=resident.name,
                        energy=state["energy"], safety=state["safety"], growth=state["growth"])
