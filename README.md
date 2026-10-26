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

## Current status: first AI resident verified locally and on a test ECS

- Resident identity, needs, and a small action vocabulary.
- World Director as the single policy and event-scheduling point.
- SQLite append-only event records.
- Mock runtime for repeatable local runs.
- DSH integration seam documented; no fictional DSH runtime API is assumed.
- Local HTTP service with health/readiness, resident create/read, action submission, and event query routes.
- Local browser page for resident creation, state, actions, recent events, and manual world turns. Rule turns choose actions through a fixed Mock policy; AI turns and dialogue require a configured model.
- First AI resident path: persona and current state prompt, persistent recent conversation, direct DeepSeek connection, AI action proposals validated by World Director, and clear connection status in the browser. A real DeepSeek dialogue and AI turn have been verified locally and on the isolated test ECS; see the [local acceptance record](docs/first-ai-resident-acceptance.md) and [server acceptance record](docs/server-acceptance-2026-10-26.md).
- Opt-in autonomous life: Mori can choose an action on a timed local schedule, based on state, recent conversation, and world events. The browser shows the selected resident, interval, daily API cap, next run, and pause control. It is disabled after every service restart.
- QQ mobile interaction: Compose includes an optional NapCat service behind the `qq` profile. It uses a private service network, persistent QQ/config volumes, a loopback-only WebUI port, and the OneBot v11 adapter. See [Linux QQ bridge setup](docs/qq-onebot-bridge.md).
- Resident state and state-changing action events persist in SQLite; the service reloads resident state after restart.
- External DSH bundle provides resident listing, event queries, and action submission through the conversation tool UI.
- Docker Compose and Dockerfile have been built and run on the isolated Alibaba Cloud Linux test ECS. The service is healthy and remains bound to server loopback.

The standard-library unit and HTTP integration suite passed 28 tests covering conversation persistence, a local fake-model HTTP exchange, AI action blocking, and in-memory key handling. The DSH HTTP client passed 4 Node tests. The container build and live service were verified on the test ECS.

The DSH bundle was installed into a disposable `DSH_HOME` under `work/`; DSH's config dump included the bundle, and its web process started without plugin load errors. A model-driven tool call was not exercised because that would require configuring an LLM account in the isolated profile.

The service listens on loopback by default. Compose binds the browser service and NapCat WebUI to host loopback; NapCat's OneBot port is private to the Compose network. There is no authentication on the browser service yet; do not expose it to a LAN or the internet. The test ECS has not been opened for phone or public-web access. The QQ/NapCat profile remains a separate setup step.

### Connect DeepSeek to Mori

Start the service and open its local browser page. DeepSeek's current [official API guide](https://api-docs.deepseek.com/guides/search_fetch) lists `https://api.deepseek.com` and `deepseek-flash`; these are the service defaults. Enter your DeepSeek API key in the page's password field and click **Connect DeepSeek**. With **保存到本机配置** selected, it is stored as plain text in the local, Git-ignored `.env` and automatically loaded after restart. In the Compose deployment it is stored in `/app/data/.env`, inside the persistent data volume. The page can also remove that saved key. The status endpoint and browser never return the key. Clicking **Send** or **AI Advance Day** sends the message, recent conversation, and relevant resident state to DeepSeek. No model call occurs when the key is absent.

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
| Sprint 1 — usable local service | Resident persistence, loopback HTTP API, action and event queries, input validation, health/readiness, SQLite schema version | 8 unit/integration tests pass, including restart recovery; Compose is validated on the isolated test ECS |
| Sprint 2 — DSH desktop plugin | Separate installable DSH bundle/profile plugin using the real plugin contract in `E:\deepseek-harness`; its tools call the local Cyber Habitat service | Bundle install, config composition, and web startup verified in an isolated profile; actual model-driven tool call and returned state still need a configured model |
| Sprint 3 — first AI resident, then richer simulation | Persona, persistent conversation, model proposals with deterministic validation and audit records; later relationships and event controls | Real DeepSeek conversation and a validated AI action pass locally and on the test ECS; timed autonomy remains opt-in |
| Sprint 4 — deployment readiness | Container build, persistent storage, health checks, backup/restore procedure, secrets and network configuration review | Image build, persistent resident state, DeepSeek dialogue, AI turn, and health checks pass on the isolated test ECS; backup/restore and phone access remain open |

Each sprint should update tests and docs alongside behavior. Keep the deterministic mock runtime available for offline development. Treat the existing DSH checkout at `E:\deepseek-harness` (commit `d347e703`) as read-only reference until an integration package is developed separately.

## Configuration

Copy `.env.example` to `.env` only when needed. The sample contains no secrets. The CLI accepts `--db` and `--seed`; the service also reads `HABITAT_HOST`, `HABITAT_PORT`, `DATABASE_PATH`, and `WORLD_RANDOM_EVENT_CHANCE`.

## Data and safety

Events are stored in the selected SQLite database. The service accepts loopback HTTP requests. When DeepSeek is configured, an explicit conversation, AI turn, or opted-in scheduled turn sends the user's message, recent conversation, and relevant resident state to DeepSeek. The API key is stored in the ignored local `.env` or, for the test ECS, the private persistent data volume; never commit or log it. Do not put secrets into world events or action details. Back up the database before manually editing it.

## Layout

- `src/cyber_habitat/`: domain model, director, event store, mock runtime, CLI.
- `tests/`: standard-library unit and loop tests.
- `docs/`: architecture decision, reuse audit, and core interface contract.
- `integrations/dsh-plugin/`: external DSH bundle for resident/event queries and action submission.
- `compose.yaml` and `Dockerfile`: built and health-checked on the isolated test ECS; see the server acceptance record for the exact boundary.
- Git: local repository on `main`; use small commits at completed milestones. No remote is configured.
