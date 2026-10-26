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

The service listens on loopback by default. Compose binds the browser service and NapCat WebUI to host loopback; NapCat's OneBot port is private to the Compose network. There is no authentication on the browser service yet; do not expose it to a LAN or the internet. The test ECS is not a production migration. NapCat is now running, but its OneBot HTTP Server/Client setup, bot-account QR login, secure local tunnel, and phone QQ round trip remain unverified. Alibaba Cloud Session Manager must be enabled by the account holder before the protected tunnel can be opened.

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

## Initial development plan (historical phases)

Work proceeds locally on Windows/WSL2, under Git, with the existing DSH source checkout used for reference. Server deployment comes only after the local service and integration pass acceptance checks. Do not modify the DSH checkout or any production server as part of local development. The more complete current product goals and roadmap below supersede any older phase wording in this historical table.

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
- Git: local repository on `main`; use small commits at completed milestones. The requested target is `https://github.com/breeze-wind/ds_fatfish_town.git`; the repository is readable but the currently connected GitHub integration reports no push permission. Do not push to another account or repository.

## Product north star and user requirements

This section consolidates decisions and observations from the project conversation so a new AI can take over without asking the user to repeat settled requirements.

### The experience to build

Cyber Habitat should feel like a small, persistent place with actual inhabitants. A user can visit the browser or write from a phone, but Mori should not need the user to repeatedly ask what he is doing. The resident should usually choose a sensible next activity on his own, take it, and leave a trace that the user can observe later. Sometimes the most appropriate choice is quiet rest; autonomy does not mean producing a new message or spectacle every minute.

Mori is the first complete resident, not a temporary demo NPC. His identity and temperament should persist across restarts. He should have a short-term intention, needs that affect decisions, meaningful memories of prior conversations/events, and enough behavioral variety to avoid looping the same activity. His actions should be concrete in the world: creating something leaves an artifact or progress; exploring can discover a place/object; resting changes energy; socializing affects a relationship. Do not mark an action complete if no state or world fact changes.

The environment may produce visitors, artifacts, weather, and other events, but events need a measured cadence and relevance. The first live log showed repeated `创作`/`休息` outcomes and recurring visitor/discovery/weather messages. Treat that as a product bug to fix with cooldowns, event budgets, duplicate detection, and contextual selection—not as desired lively behavior. Conversation should also use recent memory to avoid repeating the same “闲逛/发呆” answer in adjacent exchanges.

### Confirmed choices

- **Autonomy first:** Mori should make most day-to-day decisions himself. Chat is an available relationship channel, not a command loop.
- **First resident first:** finish one relatively complete AI resident before multiplying residents or adding broad world systems.
- **DeepSeek direct connection:** the user agreed that explicit Send/AI Advance actions may send the relevant user message, recent chat, and resident state to DeepSeek. Keep model calls visible and bounded. Timed autonomy stays disabled by default and is opt-in.
- **Phone sync matters:** the user specifically asked to prioritize QQ or another phone-synchronized channel. Current path is QQ private messages through NapCat and OneBot v11, using a separate bot account.
- **DSH is the user's desktop GUI/source project:** the user has the DSH graphical application and remembers compiling its source. Inspect/reuse what is already installed; do not waste time downloading another duplicate or treat the GUI as a headless simulation engine. The DSH bundle is optional.
- **Linux is the server OS:** develop and verify locally first, then deploy through Docker Compose to an isolated Linux test ECS. Do not write code directly on production.
- **Work to closure:** do not stop at a plan or halfway implementation. Continue until the current slice runs and has evidence, unless a real account/login, cost, security, or production boundary requires the user's action. Report the exact dependency and preserve a resumable handoff.
- **GitHub handoff:** the user intends to send this repository to the `breezewind` GitHub account and have other AI agents continue. The connected GitHub identity is currently different; reconnect the correct account before pushing.

### What counts as a complete resident action

For each action, require an observable chain:

1. Mori's needs, current intention, memory, world context, and available opportunities lead to a proposed choice.
2. The choice has a short reason tied to his situation; if it is a model proposal, it is parsed as untrusted data.
3. World Director applies limits, cooldowns, safety rules, and world preconditions.
4. The runtime changes resident/world state (or records a meaningful no-op such as a deliberate pause).
5. SQLite records intention, decision, result, and any created artifact/event.
6. The UI and QQ path can show what happened without exposing internal credentials.

If any link is missing, document it as incomplete. Do not equate an `action.applied` event with satisfying the user experience unless the underlying world effect is present and durable.

## Expanded product roadmap and acceptance gates

Roadmap order reflects the user's priority: first Mori's independent life, then the phone interaction loop that lets the user keep contact from QQ. Work should remain in small, testable commits; these gates can overlap only when doing so does not delay the first usable resident.

### A. First resident quality: Mori can live without prompts

- Write Mori's stable persona as explicit, editable project data: voice, interests, boundaries, habits, dislikes, current personal aims, and what he does when tired or uncertain.
- Separate durable memories (identity and important user/relationship facts), episodic memories (specific past events/conversations), and short-lived context (recent turns and current scene). Add retrieval rules and a maximum context budget.
- Give each resident a current intention and a small goal stack. Reconsider goals when needs, obstacles, recent outcomes, or user contact materially change; do not ask the model to invent a fresh goal every scheduler tick.
- Have the World Director own simulated time, activity windows, action availability, energy costs, recovery, cooldowns, and random-event budgets.
- Make repeated-action control explicit: recent action history, per-action cooldown, consecutive-repeat threshold, and fallback to rest/observe/continue a goal. Ensure a model cannot avoid the cooldown by changing its reason string.
- Replace fake activity spam with a small number of purposeful scheduled turns. A turn may intentionally yield “no meaningful action yet”; persist why and do not call the API again immediately.
- Add quality checks for action fit, state usefulness, persona consistency, repetition, and whether dialogue acknowledges recent context.
- Acceptance: with no incoming messages, Mori independently makes a varied series of state-appropriate choices over multiple turns; every actual action has a durable effect; repeated turns do not flood the event feed; after restart Mori recalls relevant prior context.

### B. Phone QQ: same Mori, same memory, private conversation

- Complete the missing Session Manager account setting and use an encrypted local port forward to the NapCat WebUI; keep host binding at `127.0.0.1`.
- Log in to NapCat only by QR using the dedicated bot account. Never place its password in `.env`, scripts, prompts, logs, handoff, or GitHub.
- Configure OneBot HTTP Server at container port `5700` and an HTTP Client callback to the service. Use distinct inbound/outbound tokens and persist NapCat's own config volume.
- Restrict inbound event handling to private text messages from the configured phone sender. Reject groups, other senders, self messages, duplicate event IDs, invalid tokens, and malformed payloads.
- Send inbound text through the same Mori conversation/memory service used by the browser and send the answer back through OneBot; record channel and event IDs for traceability without logging secrets.
- Acceptance: send a real short private message from the phone, observe a single correlated event, Mori's answer returns to the same QQ conversation, and browser history shows the same dialogue. Restart both containers and repeat to verify persistence.

### C. Shared world and interaction clarity

- Show resident intention, status/needs, current location/activity, recent memory-derived explanation, and a readable timeline.
- Let a human message interrupt respectfully: preserve current goals where appropriate, update the plan when the message is important, and resume autonomous life after the conversation.
- Give random events rate limits and persistent identities. Prevent duplicate visitors/finds/weather within a window; ensure world events do not falsely claim a human or external system acted.
- Make visitor/ambient events influence the resident only through documented world facts; don't flood Mori's private timeline with world noise.
- Later add rooms/places, created artifacts, found objects, relationships, and multiple residents only when a resident behavior can use them and the user can observe the result.

### D. Test ECS safety and eventual production readiness

- Current isolated test path: `/opt/cyber-habitat-test-20261025` on Alibaba Cloud Linux 3. It has the base service and NapCat running; OneBot integration reports configured, but QQ login/HTTP connections/round trip are not done.
- Keep web UI `127.0.0.1:8765`, NapCat WebUI `127.0.0.1:6099`, and OneBot `5700` private to the Docker network. Do not open a security-group port as a shortcut.
- Before any production use, add authentication, explicit authorization, rate limits, backup/restore drills, persistent-volume lifecycle, image pinning, log redaction, upgrade/rollback, and clear model cost limits.
- Never call this test ECS “production,” and never transfer live user content to another host/model without the user's established data-flow consent.

### E. Optional DSH integration

The existing checkout was identified at `E:\deepseek-harness` with commit `d347e703908d0406b7a7ef80e3a0e594d86b2215`; a packaged desktop app exists under `E:\dsh`. The local DSH bundle was installed in a disposable profile and the web process started. Preserve these as an optional integration point, not a runtime dependency. A future agent may test a model-driven tool invocation only with an appropriately configured isolated profile. Don't copy DSH `node_modules` or `.dsh-build` into this repository.

## Multi-AI collaboration quick contract

This is the short version of the repo-level rules in `AGENTS.md`:

1. At every task start, read the project guidance and `AI_HANDOFF.md`, inspect `git status`, then attempt `git fetch --all --prune` and integrate the latest branch without discarding local work.
2. Make the smallest complete vertical change. Prefer independent branches/worktrees if multiple agents work at once; coordinate ownership before editing shared core contracts.
3. Decide ordinary implementation disagreements from the accepted architecture and user decisions. If a disagreement changes product behavior, data sharing, identity/security, cost, public exposure, production operation, or no constraint resolves it, ask the user and pause only that dependent action.
4. If you modify code another AI owned or introduced, append a dated entry to `AI_CHANGE_NOTICE.md` naming that code and the reason, behavior/API effects, tests, and next owner. Do not silently overwrite another agent's work.
5. Before marking a task done, run relevant tests, inspect the diff and secret exposure, commit the finished slice, attempt a timely GitHub push to the correct account, and update `AI_HANDOFF.md` with exact evidence and next actions.
6. If GitHub is unavailable or authenticated as the wrong identity, do not push elsewhere. Preserve commits locally and state precisely what account/permission is needed.

The handoff must make it possible for a new AI to act on the next step without re-reading the entire conversation or asking the user to repeat settled preferences.
