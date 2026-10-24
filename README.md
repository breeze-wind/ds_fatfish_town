# Cyber Habitat

Cyber Habitat is a local-first simulation core for a persistent digital world. The World Director is the single authority for action policy, scheduled events, and state changes. Sprint 0 has a working local loop: a resident submits an action, deterministic safety rules allow or block it, the mock runtime changes state, and SQLite records the outcome.

## Quick start

Requires Python 3.11+; the core uses only the standard library.

```powershell
cd work/cyber-habitat
$env:PYTHONPATH = "src"
python -m cyber_habitat --db data/world.sqlite3 serve
# Open http://127.0.0.1:8765/ in a browser to create residents, advance a day, and interact.
# In another terminal:
Invoke-RestMethod http://127.0.0.1:8765/healthz
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/residents -ContentType 'application/json' -Body '{"id":"mori","name":"Mori"}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/residents/mori/actions -ContentType 'application/json' -Body '{"kind":"learn"}'
Invoke-RestMethod http://127.0.0.1:8765/residents
Invoke-RestMethod http://127.0.0.1:8765/events
```

Run the demo and unit tests with:

```powershell
python -m cyber_habitat --db data/demo.sqlite3 --seed 7 demo
python -m unittest discover -s tests -v
```

The demo creates a resident, accepts a harmless action, blocks a hazardous action, and emits a scheduled event. Re-running with the same seed makes random event selection reproducible. The database is local and can be removed to reset the demo world.

## Current status: first AI resident path implemented locally

- Resident identity, needs, and a small action vocabulary.
- World Director as the single policy and event-scheduling point.
- SQLite append-only event records.
- Mock runtime for repeatable local runs.
- DSH integration seam documented; no fictional DSH runtime API is assumed.
- Local HTTP service with health/readiness, resident create/read, action submission, and event query routes.
- Local browser page for resident creation, state, actions, recent events, and manual world turns. Rule turns choose actions through a fixed Mock policy; AI turns and dialogue require a configured model.
- First AI resident path: persona and current state prompt, persistent recent conversation, direct DeepSeek connection, AI action proposals validated by World Director, and clear connection status in the browser. A real DeepSeek dialogue and AI turn have been verified locally; see [acceptance record](docs/first-ai-resident-acceptance.md).
- Resident state and state-changing action events persist in SQLite; the service reloads resident state after restart.
- External DSH bundle provides resident listing, event queries, and action submission through the conversation tool UI.
- Docker Compose and Dockerfile prepared for later validation. They have not been built or run.

The standard-library unit and HTTP integration suite passed 18 tests covering conversation persistence, a local fake-model HTTP exchange, AI action blocking, and in-memory key handling. The DSH HTTP client passed 4 Node tests. Docker is unavailable in the current shell, so the container configuration remains unverified.

The DSH bundle was installed into a disposable `DSH_HOME` under `work/`; DSH's config dump included the bundle, and its web process started without plugin load errors. A model-driven tool call was not exercised because that would require configuring an LLM account in the isolated profile.

The service listens on loopback by default. The Compose mapping also binds only to host loopback. There is no authentication yet; keep it local and do not expose the service to a LAN or the internet.

### Connect DeepSeek to Mori

Start the service and open its local browser page. DeepSeek's current [official API guide](https://api-docs.deepseek.com/guides/search_fetch) lists `https://api.deepseek.com` and `deepseek-flash`; these are the service defaults. Enter your DeepSeek API key in the page's password field and click **Connect DeepSeek**. The key remains only in server memory and is lost at restart. The status endpoint and browser never return the key. Clicking **Send** or **AI Advance Day** sends the message, recent conversation, and relevant resident state to DeepSeek. No model call occurs when the key is absent.

You may instead set `DEEPSEEK_API_KEY` or `HABITAT_AI_API_KEY` in the service process environment. Do not paste the key into chat or commit it. Automated tests use a fake local model and mocked requests; a separate manual acceptance check used the real DeepSeek API.

### Alternative local model

Set these variables in the shell that starts `serve` (the URL is an example of a local OpenAI-compatible server; no such server is installed or running here):

```powershell
$env:HABITAT_AI_BASE_URL = 'http://127.0.0.1:11434/v1'
$env:HABITAT_AI_MODEL = 'your-installed-model'
# For a provider requiring a key, set HABITAT_AI_API_KEY in the shell, never in a tracked file.
python -m cyber_habitat --db data/world.sqlite3 serve
```

For other remote providers, use an HTTPS base URL and a process environment API key. The existing DSH desktop profile is not automatically shared with this standalone service.

## Local API

See [service API contract](docs/service-api.md) for routes, request fields, limits, and response codes. Every action passes through World Director rules. `attack` is accepted as a known action kind so the Director can record and deny it; unknown kinds are rejected before dispatch.

## Development plan

Work proceeds locally on Windows, under Git, with the existing DSH source checkout used for reference. Server deployment comes only after the local service and integration pass acceptance checks. Do not modify the DSH checkout or any production server as part of local development.

| Phase | Work | Acceptance |
|---|---|---|
| Sprint 0 — simulation core | Resident model, World Director rules and seeded events, SQLite event log, mock runtime, CLI demo | Unit tests pass; demo records resident creation, allowed action, random event, and blocked harmful action |
| Sprint 1 — usable local service | Resident persistence, loopback HTTP API, action and event queries, input validation, health/readiness, SQLite schema version | 8 unit/integration tests pass, including restart recovery; Compose still needs validation |
| Sprint 2 — DSH desktop plugin | Separate installable DSH bundle/profile plugin using the real plugin contract in `E:\deepseek-harness`; its tools call the local Cyber Habitat service | Bundle install, config composition, and web startup verified in an isolated profile; actual model-driven tool call and returned state still need a configured model |
| Sprint 3 — first AI resident, then richer simulation | Persona, persistent conversation, model proposals with deterministic validation and audit records; later relationships and event controls | The first AI path is implemented and fake-model tested; real model conversation remains to be verified once a model endpoint is configured |
| Sprint 4 — deployment readiness | Container build, persistent storage, health checks, backup/restore procedure, secrets and network configuration review | Compose build and local container acceptance pass; restore is demonstrated; deployment checklist is reviewed before any server action |

Each sprint should update tests and docs alongside behavior. Keep the deterministic mock runtime available for offline development. Treat the existing DSH checkout at `E:\deepseek-harness` (commit `d347e703`) as read-only reference until an integration package is developed separately.

## Configuration

Copy `.env.example` to `.env` only when needed. The sample contains no secrets. The CLI accepts `--db` and `--seed`; the service also reads `HABITAT_HOST`, `HABITAT_PORT`, `DATABASE_PATH`, and `WORLD_RANDOM_EVENT_CHANCE`.

## Data and safety

Events are stored in the selected local SQLite file. The service accepts loopback HTTP requests; it does not call external services. No credentials or server access are used. Do not put secrets into world events or action details. Back up the database before manually editing it.

## Layout

- `src/cyber_habitat/`: domain model, director, event store, mock runtime, CLI.
- `tests/`: standard-library unit and loop tests.
- `docs/`: architecture decision, reuse audit, and core interface contract.
- `integrations/dsh-plugin/`: external DSH bundle for resident/event queries and action submission.
- `compose.yaml` and `Dockerfile`: deployment preparation only; not yet validated in Docker.
- Git: local repository on `main`; use small commits at completed milestones. No remote is configured.
