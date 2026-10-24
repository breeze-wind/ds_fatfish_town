# Cyber Habitat

Cyber Habitat is a local-first simulation core for a persistent digital world. The World Director is the single authority for action policy, scheduled events, and state changes. Sprint 0 has a working local loop: a resident submits an action, deterministic safety rules allow or block it, the mock runtime changes state, and SQLite records the outcome.

## Quick start

Requires Python 3.11+; the core uses only the standard library.

```powershell
cd work/cyber-habitat
$env:PYTHONPATH = "src"
python -m cyber_habitat --db data/world.sqlite3 --seed 7 demo
python -m unittest discover -s tests -v
```

The demo creates a resident, accepts a harmless action, blocks a hazardous action, and emits a scheduled event. Re-running with the same seed makes random event selection reproducible. The database is local and can be removed to reset the demo world.

## Current status: Sprint 0 complete

- Resident identity, needs, and a small action vocabulary.
- World Director as the single policy and event-scheduling point.
- SQLite append-only event records.
- Mock runtime for repeatable local runs.
- DSH integration seam documented; no fictional DSH runtime API is assumed.
- Docker Compose and Dockerfile prepared for later validation. They have not been built or run.

## Development plan

Work proceeds locally on Windows, under Git, with the existing DSH source checkout used for reference. Server deployment comes only after the local service and integration pass acceptance checks. Do not modify the DSH checkout or any production server as part of local development.

| Phase | Work | Acceptance |
|---|---|---|
| Sprint 0 — simulation core | Resident model, World Director rules and seeded events, SQLite event log, mock runtime, CLI demo | Unit tests pass; demo records resident creation, allowed action, random event, and blocked harmful action |
| Sprint 1 — usable local service | Resident/world persistence, action and event query interfaces, input validation, service health/readiness, configuration and migration rules | Start locally, create/read a resident, submit actions, restart, and verify persisted state; unsafe actions remain blocked |
| Sprint 2 — DSH desktop plugin | Implement a separate installable DSH bundle/profile plugin using the real plugin contract in `E:\deepseek-harness`; have its UI call the local Cyber Habitat service | Plugin installs in a test DSH profile; displays world/resident state and submits an action; service policy is still authoritative; DSH source tree remains unchanged |
| Sprint 3 — richer simulation and AI proposals | Multiple residents, needs/relationships, event scheduling controls, optional AI action/event proposals with deterministic validation and audit records | Seeded scenarios reproduce; invalid or harmful AI proposals are rejected and logged; AI cannot write state directly |
| Sprint 4 — deployment readiness | Container build, persistent storage, health checks, backup/restore procedure, secrets and network configuration review | Compose build and local container acceptance pass; restore is demonstrated; deployment checklist is reviewed before any server action |

Each sprint should update tests and docs alongside behavior. Keep the deterministic mock runtime available for offline development. Treat the existing DSH checkout at `E:\deepseek-harness` (commit `d347e703`) as read-only reference until an integration package is developed separately.

## Configuration

Copy `.env.example` to `.env` only when needed. The sample contains no secrets. The current CLI accepts `--db` and `--seed`; Compose reserves `DATABASE_PATH` for a later packaged runtime.

## Data and safety

Events are stored in the selected local SQLite file. No telemetry, network calls, credentials, or server access are used by the Sprint 0 core. Do not put secrets into world events. Back up the database before manually editing it.

## Layout

- `src/cyber_habitat/`: domain model, director, event store, mock runtime, CLI.
- `tests/`: standard-library unit and loop tests.
- `docs/`: architecture decision, reuse audit, and core interface contract.
- `compose.yaml` and `Dockerfile`: deployment preparation only; not yet validated in Docker.
- Git: local repository on `main`; use small commits at completed milestones. No remote is configured.
