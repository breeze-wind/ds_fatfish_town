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
- Branch: `main`, tracking `origin/main`.
- Documentation/handoff commit: `649ecfe` (`Document product vision and multi-agent handoff`). Earlier milestones: `28cb079` (NapCat service startup record), `c8ccb97` (OneBot identity/configuration record), `2af592c` (QQ resident ID guidance), `561d7ae` (test ECS DeepSeek defaults/acceptance), `67410be` (QQ bridge deployment profile).
- `.env` is Git-ignored and untracked. Re-run a secret scan (`git grep -E 'sk-|LTAI|AKIA|gh[pousr]_'` and `git log -p --all`) before publishing any later diff; the scan on 2026-10-26 found no credential strings in the tracked tree or history.
- The requested target is `https://github.com/breeze-wind/ds_fatfish_town.git` (`breeze-wind/ds_fatfish_town`). Local `origin` points here. **Push now works:** on 2026-10-26 the entire `main` history (21 commits, HEAD `aa52d99`) was pushed, `main` was set to track `origin/main`, `git ls-remote origin` returned exactly the local `HEAD` SHA for both `HEAD` and `refs/heads/main`, and `GET https://api.github.com/repos/breeze-wind/ds_fatfish_town` reports `private: false`, `default_branch: main`, `pushed_at: 2026-10-26T12:27:06Z`. The older "connected account has no write permission" blocker is resolved and obsolete.
- Network note for this Windows host: plain `git fetch`/`git push` to `github.com` failed with `Failed to connect to github.com port 443 after ~21s: Could not connect to server` while `curl https://github.com/` and `https://api.github.com/` succeeded. The connection establishes over TLS and then stalls on the negotiated HTTP/2 stream; the repo-local, untracked setting `git config http.version HTTP/1.1` makes fetch and push succeed. Re-apply it after a fresh clone. Even with that setting, individual `git fetch`/`push`/`ls-remote` calls intermittently fail with `Recv failure: Connection was reset`; retrying the same command 2-3 times has always succeeded within seconds, so retry before reporting a network blocker. Never ask for or store a password/token in chat or tracked files.
- Continue pushing to that repository only, and verify `git ls-remote origin` against local `HEAD` after each push (retry the `ls-remote` if it resets).

### Verified server state

- Isolated Alibaba Cloud Linux 3 test path: `/opt/cyber-habitat-test-20261025`.
- `cyber-habitat` Compose service has been healthy on `127.0.0.1:8765`; real DeepSeek dialogue and an AI action turn were previously verified.
- OneBot integration status returns `configured=true` and Mori's full resident ID. The phone sender and tokens are only in private server configuration; do not copy them into this file.
- NapCat image was pulled via mirror and its Compose container is running. Its WebUI responds on server loopback `127.0.0.1:6099`. OneBot HTTP port `5700` is not host-published.
- NapCat HTTP Server/Client are not yet configured in the UI. Bot QQ QR login and a real phone-to-bot message round trip are not verified.
- Alibaba Cloud Session Manager is disabled for this ECS. The account holder must enable it in the ECS console before a local secure port forward can reach `6099`. Do not open the WebUI or OneBot port to the public internet to bypass this.
- Database backup/restore and production security hardening remain unverified. This is a test deployment, not production.

### Current development priorities

1. ~~Push the local `main` branch to `breeze-wind/ds_fatfish_town`~~ — done 2026-10-26 (21 commits, remote `main` matches local `HEAD`). Keep committing and pushing each finished slice.
2. Resume the QQ loop after the account holder enables Session Manager: establish local tunnel, configure NapCat HTTP Server/Client with distinct tokens, scan QR with the separate bot account, then run and record a real private-message round trip.
3. Improve Mori's self-directed life: memory continuity, meaningful action effects, goal progress, action cooldowns, less repetitive dialogue, and controlled world-event cadence.
4. Run database backup/restore acceptance on the isolated ECS.
5. Only then consider additional residents or production-readiness work.

### Local verification boundary

- Verified on 2026-10-26 in this working tree: `python -m unittest discover -s tests -v` ran **28 tests, OK** (5 `test_ai`, 1 `test_autonomy`, 3 `test_onebot`, 12 `test_service`, 7 `test_world_loop`), and `node tests/test_dsh_plugin.mjs` reported **4 pass, 0 fail**. `pytest` is not installed on this machine, so the standard-library runner is the supported path; `tests/__init__.py` was added so plain `unittest discover -s tests` works as the README documents.
- Local HTTP smoke test on 2026-10-26 (temporary DB, loopback only): `GET /healthz` → `{"status":"ok"}`; `POST /residents` created `mori-smoke`; `POST /residents/mori-smoke/actions` with `learn` was allowed (`energy 70→60`, `growth 20→32`, `action.applied`); `attack` was denied with `harmful actions are disabled` and recorded `action.blocked`; `GET /events` returned the 3 events. The service process was stopped afterwards and the temporary DB lives outside the repo.
- Use `git diff --check` before a commit, then inspect `git status`, secrets, and the diff. Do not claim tests were rerun unless they actually were.
- Push evidence for this handoff: commit `aa52d99` (`Record GitHub push permission blocker`) plus the follow-up documentation commit at the tip of `main`; both are on `origin/main` and `git ls-remote origin` matches local `HEAD`.

## Per-task update template

Append a new dated snapshot or replace the current snapshot after preserving essential prior blockers:

- Goal and status:
- Changes/files and commit:
- Tests/commands and actual results:
- Remote state/deploy evidence:
- Open blockers or user action:
- Next concrete step:
