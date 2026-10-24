import unittest
from pathlib import Path
import shutil
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cyber_habitat.director import WorldDirector
from cyber_habitat.domain import Action, ActionKind, Resident
from cyber_habitat.runtime import MockRuntime
from cyber_habitat.store import SQLiteEventStore


class WorldLoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(__file__).resolve().parents[1] / "work" / uuid.uuid4().hex
        self.temp.mkdir(parents=True)
        self.store = SQLiteEventStore(self.temp / "test.sqlite3")
        self.director = WorldDirector(MockRuntime(), self.store, seed=13, random_event_chance=0)
        self.resident = Resident("r1", "Mori")
        self.director.add_resident(self.resident)

    def tearDown(self):
        self.store.close()
        shutil.rmtree(self.temp)

    def test_allowed_action_changes_resident_and_is_persisted(self):
        decision = self.director.submit("r1", Action("r1", ActionKind.LEARN))
        self.assertTrue(decision.allowed)
        self.assertEqual(self.director.residents["r1"].growth, 32)
        events = self.store.list_events()
        self.assertEqual([event.event_type for event in events], ["resident.created", "action.applied"])

    def test_harmful_action_is_blocked_without_runtime_effect(self):
        decision = self.director.submit("r1", Action("r1", ActionKind.ATTACK))
        self.assertFalse(decision.allowed)
        self.assertEqual(self.director.residents["r1"], self.resident)
        self.assertEqual(self.store.list_events()[-1].event_type, "action.blocked")

    def test_random_event_is_seeded_and_persisted(self):
        director = WorldDirector(MockRuntime(), self.store, seed=5, random_event_chance=1)
        director.add_resident(Resident("r2", "Ari"))
        result = director.submit("r2", Action("r2", ActionKind.REST))
        self.assertTrue(any(event.event_type.startswith("world.") for event in result.events))
        self.assertEqual(len(self.store.list_events()), 4)

    def test_identity_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            self.director.submit("r1", Action("r2", ActionKind.REST))

    def test_bounds_enforced(self):
        with self.assertRaises(ValueError):
            Resident("bad", "Bad", energy=101)

    def test_tick_chooses_actions_and_records_turn(self):
        self.director.add_resident(Resident("r2", "Ari", energy=35, growth=70))
        events = self.director.tick()
        self.assertEqual(self.director.residents["r1"].growth, 32)
        self.assertEqual(self.director.residents["r2"].energy, 50)
        self.assertEqual([event.event_type for event in events],
                         ["action.applied", "action.applied", "world.tick"])
        self.assertEqual(events[-1].payload["residents"], 2)


if __name__ == "__main__":
    unittest.main()
