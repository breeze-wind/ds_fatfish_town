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

## Boundaries

- This is an isolated test deployment, not a production migration.
- The service and optional NapCat WebUI bind to host loopback. The service has no authentication and is not exposed to the public internet.
- The resident is present and can talk or take AI turns. Timed autonomy remains opt-in, so no recurring model calls are scheduled.
- The QQ/NapCat bridge has not been started or logged into. Its OneBot status is `configured=false`; the bridge tokens and WebUI token exist, but the phone sender's QQ number is missing. The current server config's resident ID is `mori`, while the created Mori resident uses the full ID above; this must be corrected before enabling OneBot. The NapCat image is not yet cached.
- Phone QQ interaction still needs a separate bot QQ account login and a protected way for the user to reach NapCat WebUI. The OneBot port must remain private to the Compose network.

## Remaining acceptance

- Complete protected NapCat setup and a real private-message round trip from QQ on the phone.
- Verify database backup and restore on the test ECS.
- Decide on an authenticated, encrypted access route before any browser UI is exposed beyond loopback.
