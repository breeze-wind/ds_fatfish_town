import argparse
import json
import os

from .director import WorldDirector
from .domain import Action, ActionKind, Resident
from .runtime import MockRuntime
from .store import SQLiteEventStore
from .service import serve


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
    parser.add_argument("--db", default=os.environ.get("DATABASE_PATH", "data/world.sqlite3"))
    parser.add_argument("--seed", type=int, default=7)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="run one local simulation loop")
    serve_command = sub.add_parser("serve", help="run the local HTTP service")
    serve_command.add_argument("--host", default=os.environ.get("HABITAT_HOST", "127.0.0.1"))
    serve_command.add_argument("--port", type=int, default=int(os.environ.get("HABITAT_PORT", "8765")))
    args = parser.parse_args()
    if args.command == "demo":
        return run_demo(args.db, args.seed)
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    try:
        random_event_chance = float(os.environ.get("WORLD_RANDOM_EVENT_CHANCE", "0.15"))
        if not 0 <= random_event_chance <= 1:
            raise ValueError("must be between 0 and 1")
        serve(args.host, args.port, args.db, seed=args.seed,
              random_event_chance=random_event_chance)
    except (OSError, ValueError) as exc:
        parser.error(f"could not start service: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
