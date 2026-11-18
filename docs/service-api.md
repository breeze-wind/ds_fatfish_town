# Local service API (Sprint 1)

The service uses Python's standard-library HTTP server and JSON. It binds to `127.0.0.1:8765` by default. Requests are processed serially. There is no authentication or CORS support; do not expose this service beyond loopback. Compose binds the host port to `127.0.0.1` as well.

All JSON request bodies must use `Content-Type: application/json`, be a JSON object, and stay within 16 KiB. Unknown fields are rejected. Resident IDs use 1–64 ASCII letters, digits, `_`, or `-`. Names are trimmed and limited to 1–80 characters. Action detail is optional, limited to 240 characters, and stored in the event log when supplied. Keep secrets and personal data out of action detail.

## Routes

| Method and path | Request | Success response |
|---|---|---|
| `GET /healthz` | none | `200 {"status":"ok"}` when the process responds |
| `GET /readyz` | none | `200 {"status":"ok"}` when the SQLite-backed server has initialized |
| `GET /residents` | none | `200 {"residents":[...]}` |
| `GET /residents/{id}` | none | `200 {"resident":...}` or `404` |
| `GET /residents/{id}/memories` | none | `200 {"memories":[{"id":...,"content":...,"created_at":...}]}` |
| `POST /residents/{id}/memories` | `{"content":"..."}` (trimmed, 1–240 characters) | `201` with saved memory; duplicate or 20-item cap returns `409` |
| `PUT /residents/{id}/memories/{memory_id}` | `{"content":"..."}` (trimmed, 1–240 characters) | `200` with updated memory; duplicate content returns `409`, missing memory returns `404` |
| `DELETE /residents/{id}/memories/{memory_id}` | none | `200 {"deleted":true}` or `404`; removes this memory from future chat context |
| `POST /residents` | `{"name":"Mori"}`; optional `id` | `201` with resident and `resident.created` event; duplicate id is `409` |
| `POST /residents/{id}/actions` | `{"kind":"rest|learn|socialize|explore|create|attack"}`; optional `detail` | `200` with decision, current resident, and emitted events |
| `POST /world/tick` | `{}` | `200` with updated residents and events; `409` when no residents exist |
| `GET /events?limit=100` | optional limit 1–500 | `200 {"events":[...]}` in event order |
| `GET /ai/status` | none | `200` with model availability and model name, never a key |
| `POST /ai/connect` | `{"api_key":"...","remember":true}` | `200` connects the official DeepSeek endpoint; `remember=true` stores the key in ignored local `.env`, never SQLite |
| `POST /ai/disconnect` | optional `{"forget":true}` | `200` clears the in-memory key; `forget=true` also removes the saved `.env` key |
| `GET /residents/{id}/conversation` | none | `200` with the latest 30 messages |
| `POST /residents/{id}/conversation` | `{"message":"你好"}` | `200` with AI answer and `resident.spoke` event; `503` without a model |
| `POST /world/ai-tick` | `{}` | `200` with AI-proposed actions passed through World Director; `503` without a model |
| `GET /autonomy` | none | `200` with local autonomous-life status and daily call counter |
| `POST /autonomy` | `{"enabled":true,"resident_id":"...","interval_seconds":1800,"max_calls_per_day":24}` | starts or pauses opt-in autonomous life; interval 60–86400 seconds, cap 1–48 |
| `GET /integrations/onebot/status` | none | `200` reports whether the optional local QQ OneBot bridge is configured; no tokens or QQ number returned |
| `POST /integrations/onebot/events` | authorized OneBot private-message event | sends the message to the selected resident and relays its reply via local OneBot |

Action kinds outside the documented vocabulary return `400`. `attack` is a known hazardous action: it returns `200` with `decision.allowed=false` and appends `action.blocked`. Unknown residents return `404`.

## Persistence

The SQLite database is created on first launch. Schema version 4 stores resident state, current intentions, conversation messages, user-saved resident memories, and the append-only event log. Resident creation and its event are committed together; successful state-changing actions and their `action.applied` event are committed together. Memory creation/deletion also appends a corresponding event with the memory ID, never the private memory text. The World Director reloads resident records at service startup. Random world events are separate records emitted after the action commit.

There is no authentication, user account, cross-origin browser access, or multi-process concurrency guarantee. The memory deletion route removes the selected saved memory, not the original conversation message or external model provider copies; it is not a full account/data erasure endpoint.

## First AI resident

The browser can ask an OpenAI-compatible chat-completions model to speak as a resident or propose an action. The default model route is DeepSeek, but remains disconnected until a key is explicitly supplied in the local page or process environment. Other endpoints require `HABITAT_AI_BASE_URL` and `HABITAT_AI_MODEL`; put any `HABITAT_AI_API_KEY` in the process environment, never in Git. The endpoint must use HTTPS except for local loopback HTTP. Conversation history is stored in SQLite. A chat request sends the latest 12 messages, current state, up to five approved past actions for that resident, and any user-saved memories (up to 20) to the configured model. The UI explains this before memory is saved. Saved memory text is user-provided data, not a system instruction; user correction in the current turn takes precedence. AI action proposals contain a `kind`, a short `reason`, and a short current `intention`; all proposals pass through World Director, so `attack` remains blocked. Invalid proposals are recorded as `ai.proposal.rejected`. Failed model requests do not create a conversation exchange. The local HTTP server handles requests serially, so a slow model request can temporarily delay other requests.

Autonomous life is local, explicitly enabled, and is always paused after a service restart. It schedules a selected resident with a 60-second minimum interval and a per-calendar-day model-call cap. A failed model call counts against the cap to avoid retry costs. The scheduler holds no secret and sends the same state, recent conversation, and recent world events that a manual AI turn sends.
