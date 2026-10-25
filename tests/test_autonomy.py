import threading
import time
import unittest

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cyber_habitat.autonomy import AutonomousLife


class AutonomousLifeTests(unittest.TestCase):
    def test_disabled_by_default_and_respects_daily_cap(self):
        calls = []
        ready = threading.Event()

        def step(resident_id):
            calls.append(resident_id)
            ready.set()

        life = AutonomousLife(step)
        try:
            self.assertFalse(life.status()["enabled"])
            with self.assertRaises(ValueError):
                life.configure("mori", enabled=True, interval_seconds=59)
            # Set the due time directly for a fast deterministic scheduler test.
            life.configure("mori", enabled=True, interval_seconds=60, max_calls_per_day=1)
            with life._lock:
                life._next_at = time.time()
            life._wake.set()
            self.assertTrue(ready.wait(2))
            time.sleep(0.1)
            self.assertEqual(calls, ["mori"])
            self.assertEqual(life.status()["calls_today"], 1)
        finally:
            life.close()


if __name__ == "__main__":
    unittest.main()
