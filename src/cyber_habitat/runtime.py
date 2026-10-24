from .domain import Action, ActionKind, Resident


class MockRuntime:
    """Pure in-memory effect adapter used by local runs and tests."""

    def apply(self, resident: Resident, action: Action) -> Resident:
        changes = {
            ActionKind.REST: {"energy": 15},
            ActionKind.LEARN: {"energy": -10, "growth": 12},
            ActionKind.SOCIALIZE: {"energy": -5, "safety": 5},
        }.get(action.kind)
        if changes is None:
            raise ValueError(f"runtime does not implement {action.kind.value}")
        state = {"energy": resident.energy, "safety": resident.safety, "growth": resident.growth}
        for key, delta in changes.items():
            state[key] = max(0, min(100, state[key] + delta))
        return Resident(id=resident.id, name=resident.name, **state)
