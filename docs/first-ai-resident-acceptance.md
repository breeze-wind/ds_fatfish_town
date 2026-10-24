# First AI resident acceptance

Date: 2026-10-25 (Asia/Shanghai). Local Windows service only; no production server was touched.

## Verified with a real DeepSeek API connection

- The user entered the API key into the local page. `/ai/status` reported `configured=true` and `model=deepseek-flash`; the key was never printed or committed.
- Mori answered a harmless introduction request through `POST /residents/{id}/conversation`. The response carried a `resident.spoke` event. A subsequent conversation query returned two saved messages.
- `POST /world/ai-tick` produced `action.applied` and `world.ai_tick` events. The model proposed `learn`; World Director applied it, changing energy from 80 to 70 while growth remained at its cap of 100. The event query showed those records.
- 18 Python tests and 4 DSH plugin tests passed before the real API calls. The browser script parsed successfully.

## Current limits

- The model picked `learn` even though growth was already 100. Action usefulness and longer-term goals need improvement.
- AI turns are triggered by the user; there is no background autonomous schedule yet.
- The key is held in the current server process only and is lost on restart. The live DeepSeek connection was not retested after a restart.
- The DSH desktop profile is separate and was not used for this acceptance check.
