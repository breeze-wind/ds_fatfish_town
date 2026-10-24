import argparse
import json

from .director import WorldDirector
from .domain import Action, ActionKind, Resident
from .runtime import MockRuntime
from .store import SQLiteEventStore


def run_demo(db_path: str, seed: int) -> int:
    store = SQLiteEventStore(db_path)
    try:
        director = WorldDirector(MockRuntime(), store, seed=seed, random_event_chance=1.0)
        resident = Resident("resident-001", "Mori")
        director.add_resident(resident)
        accepted = director.submit(resident.id, Action(resident.id, ActionKind.LEARN))
        blocked = director.submit(resident.id, Action(resident.id, ActionKind.ATTACK))
        print(json.dumps({
            "resident": director.residents[resident.id].__dict__,
            "accepted": accepted.allowed,
            "blocked": blocked.allowed,
            "events": [event.__dict__ for event in store.list_events()],
        }, ensure_ascii=False, indent=2))
        return 0
    finally:
        store.close()


def main() -> int:
    parser = argparse.ArgumentParser(prog="cyber-habitat")
    parser.add_argument("--db", default="data/world.sqlite3")
    parser.add_argument("--seed", type=int, default=7)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="run one local simulation loop")
    sub.add_parser("serve-placeholder", help="reserved for a future server entrypoint")
    args = parser.parse_args()
    if args.command == "demo":
        return run_demo(args.db, args.seed)
    parser.error("server entrypoint is not implemented in Sprint 0")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
