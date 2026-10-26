# Test ECS acceptance record

Date: 2026-10-26 (Asia/Shanghai)  
Target: isolated Alibaba Cloud Linux 3 test directory `/opt/cyber-habitat-test-20261025`

## Verified

- The Compose image built successfully after pulling `python:3.13-slim` through a reachable mirror. The image was retagged locally on the ECS; the application Dockerfile still uses the standard Python image name.
- The service container reached Docker health status `healthy`; `/readyz` returned `{"status":"ok"}` and the browser route returned HTTP 200.
- Mori was created with resident ID `0fc96ecd46884310bd4b81612bf39f21` and persisted in the Compose data volume.
- Compose now defaults to `https://api.deepseek.com` and `deepseek-flash` when the optional variables are empty. This avoids overriding the application defaults with empty strings.
- The saved local DeepSeek key was transferred through the authenticated ECS control channel and stored by the service in `/app/data/.env`, inside the private persistent data volume. It was not added to Git or printed in command output.
- A real DeepSeek conversation returned a Chinese reply and wrote a `resident.spoke` event.
- A real AI turn produced a resident intention, an approved `explore` action, and a `world.ai_tick` event. Mori's persisted state changed from energy/safety/growth `70/70/20` to `62/68/23`.
- The test `.env` now contains the configured phone sender and Mori's full resident ID, with file mode `0600`. The app was restarted and `/integrations/onebot/status` returned `configured=true` with Mori's full ID.
- The NapCat image was pulled through the reachable DaoCloud mirror and retagged locally. Pulled manifest digest: `sha256:b101b8968cc31ae428ec0f8e117386e4ced7773b2d8226ed9f7ddfcec55f1b7e`.

## Boundaries

- This is an isolated test deployment, not a production migration.
- The service and optional NapCat WebUI bind to host loopback. The service has no authentication and is not exposed to the public internet.
- The resident is present and can talk or take AI turns. Timed autonomy remains opt-in, so no recurring model calls are scheduled.
- The NapCat container has not started and no QQ account has logged in. Starting it was blocked by Alibaba Workbench returning `403 Forbidden.SessionLimit`; reusing the last session returned `session not found`, and the local session list showed no active sessions. No more automatic retries were made to avoid consuming additional sessions.
- Phone QQ interaction still needs a separate bot QQ account login and a protected way for the user to reach NapCat WebUI. The OneBot port must remain private to the Compose network.

## Remaining acceptance

- Start NapCat in the test Compose profile after Workbench session access is available again; retain loopback-only WebUI binding.
- Configure NapCat's OneBot HTTP server/client in its protected WebUI, log in with the separate bot QQ account through QR, and verify a real private-message round trip from QQ on the phone.
- Verify database backup and restore on the test ECS.
- Decide on an authenticated, encrypted access route before any browser UI is exposed beyond loopback.
