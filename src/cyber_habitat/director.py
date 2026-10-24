import random

from .domain import Action, ActionKind, Decision, Resident, WorldEvent
from .ports import EventStorePort, RuntimePort


class WorldDirector:
    """Single authority for action policy, runtime effects, and world events."""

    def __init__(self, runtime: RuntimePort, store: EventStorePort, *, seed: int = 0,
                 random_event_chance: float = 0.15):
        if not 0 <= random_event_chance <= 1:
            raise ValueError("random_event_chance must be between 0 and 1")
        self.runtime = runtime
        self.store = store
        self.rng = random.Random(seed)
        self.random_event_chance = random_event_chance
        self.residents: dict[str, Resident] = {}
        self._random_events = (
            ("world.discovery", "A quiet corner of the habitat reveals a curious artifact."),
            ("world.weather", "A gentle aurora passes over the habitat."),
            ("world.visitor", "A friendly visitor leaves a small message."),
        )

    def add_resident(self, resident: Resident) -> WorldEvent:
        if resident.id in self.residents:
            raise ValueError(f"resident already exists: {resident.id}")
        self.residents[resident.id] = resident
        return self.store.append("resident.created", resident.id, {"name": resident.name})

    def submit(self, resident_id: str, action: Action) -> Decision:
        resident = self.residents.get(resident_id)
        if resident is None:
            raise KeyError(f"unknown resident: {resident_id}")
        if action.resident_id != resident_id:
            raise ValueError("action resident_id does not match request resident")
        if not isinstance(action.kind, ActionKind):
            raise ValueError("unknown action kind")
        if action.kind is ActionKind.ATTACK:
            event = self.store.append("action.blocked", resident_id,
                                      {"action": action.kind.value, "reason": "harmful actions are disabled"})
            return Decision(False, "harmful actions are disabled", (event,))

        updated = self.runtime.apply(resident, action)
        self.residents[resident_id] = updated
        events = [self.store.append("action.applied", resident_id, {
            "action": action.kind.value,
            "state": {"energy": updated.energy, "safety": updated.safety, "growth": updated.growth},
        })]
        if self.rng.random() < self.random_event_chance:
            event_type, description = self.rng.choice(self._random_events)
            events.append(self.store.append(event_type, "world", {"description": description}))
        return Decision(True, "action applied", tuple(events))
