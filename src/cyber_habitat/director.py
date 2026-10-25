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
        self.residents: dict[str, Resident] = {resident.id: resident for resident in store.list_residents()}
        self._random_events = (
            ("world.discovery", "A quiet corner of the habitat reveals a curious artifact."),
            ("world.weather", "A gentle aurora passes over the habitat."),
            ("world.visitor", "A friendly visitor leaves a small message."),
        )

    def add_resident(self, resident: Resident) -> WorldEvent:
        if resident.id in self.residents:
            raise ValueError(f"resident already exists: {resident.id}")
        event = self.store.create_resident(resident)
        self.residents[resident.id] = resident
        return event

    def tick(self) -> tuple[WorldEvent, ...]:
        """Advance each resident once using a small, deterministic mock policy."""
        events: list[WorldEvent] = []
        for resident_id in sorted(self.residents):
            resident = self.residents[resident_id]
            if resident.energy <= 40:
                kind = ActionKind.REST
            elif resident.growth < 60:
                kind = ActionKind.LEARN
            else:
                kind = ActionKind.EXPLORE if resident.safety >= 50 else ActionKind.SOCIALIZE
            decision = self.submit(resident_id, Action(resident_id, kind, "mock autonomous turn"))
            events.extend(decision.events)
        events.append(self.store.append("world.tick", "world", {"residents": len(self.residents)}))
        return tuple(events)

    def submit(self, resident_id: str, action: Action) -> Decision:
        resident = self.residents.get(resident_id)
        if resident is None:
            raise KeyError(f"unknown resident: {resident_id}")
        if action.resident_id != resident_id:
            raise ValueError("action resident_id does not match request resident")
        if not isinstance(action.kind, ActionKind):
            raise ValueError("unknown action kind")
        if action.kind is ActionKind.ATTACK:
            payload: dict[str, object] = {
                "action": action.kind.value,
                "reason": "harmful actions are disabled",
            }
            if action.detail:
                payload["detail"] = action.detail
            event = self.store.append("action.blocked", resident_id,
                                      payload)
            return Decision(False, "harmful actions are disabled", (event,))

        updated = self.runtime.apply(resident, action)
        action_payload = {
            "action": action.kind.value,
            "state": {"energy": updated.energy, "safety": updated.safety, "growth": updated.growth},
        }
        if action.detail:
            action_payload["detail"] = action.detail
        events = [self.store.update_resident_and_append(updated, "action.applied", action_payload)]
        self.residents[resident_id] = updated
        if self.rng.random() < self.random_event_chance:
            event_type, description = self.rng.choice(self._random_events)
            events.append(self.store.append(event_type, "world", {"description": description}))
        return Decision(True, "action applied", tuple(events))
