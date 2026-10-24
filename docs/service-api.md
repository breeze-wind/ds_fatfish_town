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
| `POST /residents` | `{"name":"Mori"}`; optional `id` | `201` with resident and `resident.created` event; duplicate id is `409` |
| `POST /residents/{id}/actions` | `{"kind":"rest|learn|socialize|attack"}`; optional `detail` | `200` with decision, current resident, and emitted events |
| `GET /events?limit=100` | optional limit 1–500 | `200 {"events":[...]}` in event order |

Action kinds outside the documented vocabulary return `400`. `attack` is a known hazardous action: it returns `200` with `decision.allowed=false` and appends `action.blocked`. Unknown residents return `404`.

## Persistence

The SQLite database is created on first launch. Schema version 1 stores resident state and the append-only event log. Resident creation and its event are committed together; successful state-changing actions and their `action.applied` event are committed together. The World Director reloads resident records at service startup. Random world events are separate records emitted after the action commit.

No authentication, user accounts, deletion route, cross-origin browser access, or multi-process concurrency guarantee is provided in Sprint 1.
