# AI Handoff

> Update this file before ending every meaningful AI work unit. It is the short, current-state entry point for the next AI; keep durable product decisions in `README.md` and detailed evidence in `docs/`.

## Snapshot — 2026-10-26

### User goal and fixed decisions

- Build Cyber Habitat around an AI resident who mostly chooses what to do himself. Complete Mori before broadening the world.
- DeepSeek direct API is approved for explicit send/AI-advance calls; context and API cost must remain bounded. Timed autonomy is opt-in and off after restart.
- Phone-synchronized interaction is a priority. Use private QQ messages through NapCat + OneBot v11 with a dedicated bot QQ account, separate from the user's phone sender.
- DSH is the user's desktop GUI and existing compiled/source project. Reuse it as an optional plugin/tool surface; do not invent a DSH runtime API or make Cyber Habitat depend on it.
- Develop locally on Windows/WSL2 with Git. The server is Linux. Use Docker Compose only for isolated testing until production deployment is separately authorized.
- The user asked for durable multi-AI collaboration: sync the newest GitHub state, attempt merges, record code overrides, and leave a handoff every time.

### Current local repository

- Project directory: `work/cyber-habitat`.
- Branch: `main`.
- Recent commits before the current README/handoff work: `28cb079` (NapCat service startup record), `c8ccb97` (OneBot identity/configuration record), `2af592c` (QQ resident ID guidance), `561d7ae` (test ECS DeepSeek defaults/acceptance), `67410be` (QQ bridge deployment profile).
- `.env` is Git-ignored. Current high-confidence scan of all 19 reachable commits found no `sk-`, `LTAI`, or `AKIA`-style credential strings. Re-run a secret scan before publishing any later diff.
- The requested target is `https://github.com/breeze-wind/ds_fatfish_town.git` (`breeze-wind/ds_fatfish_town`). GitHub confirms the public repository is readable, but the connected GitHub integration reports `push=false`; the local `origin` should point here, and agents must not push to another account or repository.
- Once the correct writable GitHub connection is available: fetch and integrate latest `main`, then push this repo's completed commits. If a private credential is needed, the account holder must reconnect or grant repo write permission; never ask for or store a password/token in chat.

### Verified server state

- Isolated Alibaba Cloud Linux 3 test path: `/opt/cyber-habitat-test-20261025`.
- `cyber-habitat` Compose service has been healthy on `127.0.0.1:8765`; real DeepSeek dialogue and an AI action turn were previously verified.
- OneBot integration status returns `configured=true` and Mori's full resident ID. The phone sender and tokens are only in private server configuration; do not copy them into this file.
- NapCat image was pulled via mirror and its Compose container is running. Its WebUI responds on server loopback `127.0.0.1:6099`. OneBot HTTP port `5700` is not host-published.
- NapCat HTTP Server/Client are not yet configured in the UI. Bot QQ QR login and a real phone-to-bot message round trip are not verified.
- Alibaba Cloud Session Manager is disabled for this ECS. The account holder must enable it in the ECS console before a local secure port forward can reach `6099`. Do not open the WebUI or OneBot port to the public internet to bypass this.
- Database backup/restore and production security hardening remain unverified. This is a test deployment, not production.

### Current development priorities

1. Finish the product README and collaboration protocol; push after the correct GitHub write identity is connected.
2. Resume the QQ loop after the account holder enables Session Manager: establish local tunnel, configure NapCat HTTP Server/Client with distinct tokens, scan QR with the separate bot account, then run and record a real private-message round trip.
3. Improve Mori's self-directed life: memory continuity, meaningful action effects, goal progress, action cooldowns, less repetitive dialogue, and controlled world-event cadence.
4. Run database backup/restore acceptance on the isolated ECS.
5. Only then consider additional residents or production-readiness work.

### Local verification boundary

- Historical results: 28 Python tests and 4 DSH Node tests passed before this documentation handoff. No code tests were rerun for the current documentation-only changes.
- Use `git diff --check` for the current docs, then inspect Git status, secrets, and commit. Do not claim tests were rerun unless they actually were.
- Next work must update this file with the actual final commit SHA and push result.

## Per-task update template

Append a new dated snapshot or replace the current snapshot after preserving essential prior blockers:

- Goal and status:
- Changes/files and commit:
- Tests/commands and actual results:
- Remote state/deploy evidence:
- Open blockers or user action:
- Next concrete step:
