# AI Handoff

> Update this file before ending every meaningful AI work unit. It is the short, current-state entry point for the next AI; keep durable product decisions in `README.md` and detailed evidence in `docs/`.

## Community 大肥鱼 animation preview — 2026-11-19

- Added optional source-checkout preview files served by `src/cyber_habitat/service.py` and selected by `src/cyber_habitat/habitat.html`. `python -X utf8 scripts/fetch_whale_preview.py` pins and fetches four transparent VP9 WebMs into a Git-ignored directory. Idle, greeting (女仆屈膝礼仪), thinking and low energy use separate clips; chat focus and the existing interaction logic are retained. The browser setting persists locally, and a missing or unsupported clip or the reduced motion setting falls back to the original Mori illustration.
- `README.md` and `THIRD_PARTY_NOTICES.md` explain how to get the preview and its CC BY-NC-SA 4.0 asset terms. Credits are shown alongside the animation. The original illustration remains the packaged asset; downloaded video bytes remain local.
- Validation: four clips downloaded and `ffprobe` identified VP9 and alpha for all four. The local service on 127.0.0.1:8765 returned 200 for health, home and all four media URLs, and 404 for an unknown clip. Edge played all four videos; the greeting click focused chat, and the preview switch restored the illustration and persisted on reload. Browser check used synthetic API responses; no model request or remote deployment. `git diff --check` passed.
- Git fetch succeeded after retry outside the sandbox. Pre-change `main` was 13 commits ahead and zero behind `origin/main`; nothing to merge. Milestone commit `217c0bf` was pushed to `breeze-wind/ds_fatfish_town` on `main` after verifying the GitHub login and checking the outgoing patch history for credential patterns. Preserve the unrelated, untracked `Start-Mori.cmd`. Next: decide whether to keep this look as reference, then create separately licensed Mori motion assets for the Android release.

## Whale-girl Mori browser redesign

- Replaced the old whale SVG with original generated whale-girl art. The transparent `src/cyber_habitat/mori.webp` is packaged with the app and served at `/mori.webp`.
- Rebuilt the home page around the illustration and chat. Chat bubble structure follows daisyUI under MIT, with attribution in `THIRD_PARTY_NOTICES.md`. The artwork and styles are local. Resident status is collapsible, and the existing model, memory, and world controls are below the chat.
- Git fetch was attempted but failed during GitHub DNS resolution. The last known `origin/main` has no remote-only commits. The unrelated local `Start-Mori.cmd` was preserved.
- Rendered the actual HTML and local WebP in Edge at 1200×830 and 390×844 with synthetic API responses. Both layouts loaded the image and conversation, had no horizontal overflow, and focused the chat input on character click. Screenshots are `mori-desktop-preview.png` and `mori-mobile-preview.png` in the parent task workspace. No live model call was made.
- A separate real HTTP check with an in-memory database returned 200 for both the homepage and the WebP route.
- Local delivery is the commit titled `Redesign Mori as a whale-girl companion`. Restart the Python service to register the new static route, then reload the page. No remote deployment.

## Editable user-controlled memories — 2026-11-18

- Code commit: `e7f844c` (`Allow editing user-saved memories`). After `git fetch origin`, `main` was 11 commits ahead of `origin/main` with no remote-only commits. Push was attempted and failed because Git Credential Manager could not start and Git had no username while terminal prompts were disabled. A follow-up documentation commit records the exact code-commit pointer and change-ledger entry; local `main` is now 12 commits ahead.
- Added `PUT /residents/{id}/memories/{memory_id}` and an inline editor in the “她记住的事” panel. Notes remain user-authored, limited to 240 characters and 20 per resident. Duplicate text returns `409`; missing notes return `404`; no-op edits do not create events. Real edits append `resident.memory_updated` with only the memory ID, preserving note privacy in the event log.
- Updated the service contract, main README feature summary, memory disclosure and event label. Automatic extraction/correction is still not implemented; the user explicitly edits the note.
- Validation boundary: no automated tests were added or run for this slice. `git diff --check` passed. Restarted the loopback service; `GET /healthz` returned `ok`. CRUD behavior for the new editor remains unverified. The existing in-app browser cannot reach the host-local listener; do not expose unauthenticated port 8765 to LAN or internet.
- Previous saved-memory milestone and real-model check remain immediately below. The real-model test used synthetic data only. Android native shell, secure phone connection, APK/device validation and GitHub write access remain open.

## Saved-memory model check and local preview — 2026-11-18

- Real-model check: passed one direct DeepSeek prompt check using only a synthetic saved note (“call the test user 小明”); the model replied “记得，你让我称呼你小明。” This confirms saved-note prompt inclusion for one request. It is not a browser end-to-end test or a reliability study; no private user data was sent. Details and limits are in `docs/mori-dialogue-design.md`.
- Temporary evaluation artifact: `.ui_memory_eval.py` was only a disposable UI harness and has been removed. The earlier fake-model UI smoke test and 34-test result remain the latest full-suite evidence; no tests were rerun for this documentation update.
- Preview: restarted the service on loopback and verified `GET http://127.0.0.1:8765/healthz` returned `ok`. The Codex in-app browser still reports `ERR_CONNECTION_REFUSED`, so its access to the host-local service is not verified. Do not expose the unauthenticated service to LAN or internet to work around that isolation.
- Git: `885964f` (`Document real model memory check`) records this documentation update. `git fetch origin` succeeded; remote had no new commits and local `main` is 10 commits ahead. `git push origin main` was retried and failed because Git Credential Manager could not start and Git had no username while terminal prompts were disabled. Keep all local commits; do not reset. GitHub still lacks these local changes.
- Next: show the user the refreshed page, collect concrete examples of unnatural dialogue, then improve Mori's persona and editable/correctable memory. Native Android shell, secure phone connection, and APK/device validation remain outstanding.

## User-controlled Mori memory — 2026-11-17

- Code milestone: `e6fabb4` (`Add user controlled resident memories`). SQLite schema v4 adds up to 20 user-saved notes per resident (240 characters each). The local API lists, adds, and deletes them; each change appends a world event containing only the memory ID, not the note. Chat prompts include saved notes as user data, and deleted notes disappear from future prompts. The browser has “她记住的事” with a clear disclosure that saved notes go to the configured model on later chats and that deleting a note does not erase original chat history. `docs/service-api.md` and `docs/mori-dialogue-design.md` describe contracts and limits.
- Verification: `python -m unittest discover -s tests -q` passed **34 tests**, including add/duplicate/cap/resident separation, prompt inclusion/removal, deletion, and restart persistence. A ResourceWarning about an unclosed socket appeared once during the suite; all tests passed and its origin was not isolated. Browser UI smoke test on a temporary fake-model server saved a synthetic note and displayed it after reload. Deletion was verified through the API test, not a browser click. `git diff --check` passed and the changed files had no high-confidence credential pattern.
- Local data migration: before opening the existing local world with new code, a consistent SQLite backup was made at `data/world.sqlite3-pre-v4-20261117.bak` (Git ignored). The restarted loopback service returned `health=ok`; the database migrated from schema 3 to 4 and still held one resident and 10 chat messages. The new memory route returned an empty list for the existing resident. The API key was not printed or committed. Temporary fake-model test processes were stopped; no Linux server or production environment changed.
- Product limits: this is manual, user-approved memory only. Mori does not automatically extract, edit, reconcile, or expire facts; recent chat still stops at 12 messages. Real-model behavior with a saved memory has not been tested. An Android APK/overlay and secure phone connection remain outstanding; the local browser page is available at `http://127.0.0.1:8765/` while the local service runs.
- Git: `origin` remains `https://github.com/breeze-wind/ds_fatfish_town.git`. `git push origin main` was attempted after this handoff and failed again because this session has no GitHub credential (`could not read Username`; prompts disabled). The connected GitHub app identity is `bding5746-del`; repository metadata reports `pull=true`, `push=false` for that identity, so the connector cannot upload this work either. Local `main` is now nine commits ahead of `origin/main`; `e6fabb4` and this handoff are **not on GitHub**. Connect a write-capable `breeze-wind` credential and push; do not reset away local commits.
- Next concrete step: have the user try the page and provide exact examples of speech that feels artificial, then tune the character profile and add memory editing/correction. Implement a repeatable conversation quality harness without auto-promoting model guesses into facts. Prepare native Android build tooling and authenticated phone access before promising an APK.

## Grounded Mori dialogue after real-model review — 2026-11-17

- Code milestone: `c606b36` (`Ground Mori dialogue in verified resident actions`), built on browser prototype `e25884a`. `store.recent_actions()` reads only this resident's approved action events; `respond_to_resident()` supplies them to `conversation_prompt()`. No HTTP endpoint or database schema changed. Old assistant messages remain dialogue context, never evidence that a physical action occurred.
- Real-model evaluation: on temporary empty residents, nine `deepseek-flash` calls were sent through the local page using only synthetic test phrases. Initial sample invented locations and objects; intermediate prompts still repeated “发呆” and asked why the user was asking. The final three-turn sample answered “干嘛呢？” twice and “你不是有创作吗？” once: it distinguished current thought from completed work, did not claim unrecorded physical actions, and did not end the repeated question with another question. This is one sampled sequence, not a controlled quality study; some language remained overly literary. No private conversation data or API key was printed. Exact token/cost data was not collected. Details: `docs/mori-dialogue-design.md`.
- Validation: `python -m unittest discover -s tests -q` passed **32 tests** after final code edits; `git diff --check` passed; high-confidence secret scan of changed files found none. The local main service was restarted on `127.0.0.1:8765` and returned `health=ok`. Temporary evaluation processes on ports 8767–8770 were stopped and their temporary databases deleted. No Linux server or online environment changed.
- Limits: backend still uses only the most recent 12 chat messages and at most five verified actions; there is no durable personal memory, autonomous thought stream, Android APK, overlay, or authenticated phone connection. UI and prompt are usable local prototypes. The user should judge whether Mori's present tone is too poetic or still robotic before a style is locked in.
- Git: this work started from local `main` five commits ahead of `origin/main`. `git push origin main` was attempted after this handoff commit and failed again: terminal prompts were disabled and Git could not read a GitHub username. Local `main` is now seven commits ahead of `origin/main`; `c606b36` and this handoff are not on GitHub. Reconnect a write-capable `breeze-wind` Git credential, then push without resetting local commits.
- Next concrete step: show the refreshed local page to the user for a few real conversations; gather exact examples of unwanted responses. Then implement an editable character profile and user-controlled memory with correction/deletion, plus a repeatable multi-seed conversation evaluation. Android native shell and secure phone access remain the larger product gate.

## Mori mobile browser prototype and dialogue tuning — 2026-11-17

- Code milestone: `e25884a` (`Build Mori chat-first browser prototype and tune dialogue`). `src/cyber_habitat/habitat.html` now shows the resident as an original inline SVG whale, stored conversation and real state. Tap focuses the input; the UI links greeting, listening, thinking, speaking and low-energy motion to actual interactions or recorded values. Previous world intention is labeled as previous rather than presented as live activity. Model/world/optional autonomy controls remain in expandable settings.
- `src/cyber_habitat/ai.py` separates general persona from chat instructions. Chat now responds to the specific topic, uses recent history to avoid repeated filler, limits gratuitous questions and forbids claims of unrecorded activity. DeepSeek non-thinking conversation temperature is 1.3 per its published general-conversation recommendation; structured JSON action temperature is 0.7. See `docs/mori-dialogue-design.md` for evidence and the planned real-model review.
- Browser proof: checked the page at 390×844 and desktop width. On a separate server with a temporary SQLite database and a fake local model, submitted one message through the page; the reply and both messages remained visible after reload. Tapping the whale focused the input and set the greeting state. This does not validate the quality of a real DeepSeek answer.
- Tests: `python -m unittest discover -s tests -q` passed **29 tests** after the prompt/parameter changes; `python -m unittest tests.test_ai -q` passed **6 tests** after the last test-fixture cleanup. `git diff --check` passed; high-confidence secret pattern scan of changed files found none. The local service at `127.0.0.1:8765` was restarted and returned `health=ok`, `residents=1` after commit. No server deployment or production change was made.
- Build limits: no Android SDK, Gradle, or connected ADB device was found on this Windows machine. This is a working mobile-sized **browser preview**, not an APK or Android overlay. The local service is unauthenticated and must stay on loopback; phone access needs authenticated HTTPS before exposure. No live DeepSeek comparison or user acceptance test of the new dialogue has been run; the configured key was not printed or committed.
- Git: `git fetch --all --prune` succeeded at task start; `origin` is `breeze-wind/ds_fatfish_town`. The branch was three commits ahead of `origin/main` before this work. `git push origin main` was attempted with interaction disabled and failed because Git has no GitHub username/credential in this session (`could not read Username`). Local `main` is five commits ahead of `origin/main`; the code and this handoff are **not yet on GitHub**. Do not discard local commits to match remote. The account holder needs to connect Git credentials for `breeze-wind` or give this workspace a write-capable GitHub connection.
- Next concrete work: run a small, cost-aware A/B review of the exact user examples in `docs/mori-dialogue-design.md` using a disposable database; adjust persona/history handling based on observed answers. Then build the native Android shell with licensed/original assets, authenticated phone connection, and device validation. Keep QQ and autonomous world behavior optional.

## Coopanion reference audit — 2026-11-17

- User provided official site `coo.palailab.org` and a Bilibili tutorial. Official source is `Pal-AI-Lab/Coopanion`; current app is a Windows/macOS/Linux Electron desktop pet assembled from Cortico, Cormini, and a desktop pet World. See the new section in `docs/reuse-audit.md` and the link in `docs/android-pet-plan.md`.
- Source inspection found a figure pack, canvas/mesh rig, springs, transparent desktop host, bubbles, and touch/drag events. Current code is AGPL-3.0-or-later; whale textures are excluded from that grant. The project README says releases through 0.1.10 were MIT, which does not license the current code as MIT. No binary was downloaded or unpacked; `electron-builder.yml` has `asar: false`, and the source is already public.
- The Bilibili page was not readable through the available web reader, so the tutorial's contents were not verified. No Cyber Habitat behavior, server, account, or test state was changed in this audit. The next implementation step remains an Android pet shell with independently sourced art and state-linked interaction; any direct source import needs file-level license review.
- `git fetch --all --prune` succeeded before these edits. Local `main` was two commits ahead of `origin/main`; the current connected GitHub identity remains read-only for the target repo.
- Documentation-only audit was committed at the current `HEAD`. `git diff --check` passed and no high-confidence credential pattern was found in the changed files; tests were not run. The push attempt returned `could not read Username` with interaction disabled, so local `main` is now three commits ahead of `origin/main` and this audit is not yet on GitHub.

## Product priority update — 2026-11-17

- User clarified that routine autonomous activity can wait. Prioritize a vivid, human-like Android desk pet and chatbot with polished UI. Use `docs/android-pet-plan.md` as the current plan; older autonomy-first/PWA-first/QQ-first statements below are historical.
- Identified the TapTap reference `小鲸鱼：会记住你的桌宠` and matching public repository `yuan10-06/xiaojingyu`. The repo has MIT code, Android source, and a GitHub release APK. Its own asset notices do not grant blanket redistribution rights for animations/Live2D/fonts. Source and exact audit links are recorded in the current plan.
- This work unit changes documentation only: README, product-direction history, new Android plan, and this handoff. No application code, tests, server, or account settings were changed. `git fetch --all --prune` succeeded; `main` was one local commit ahead of `origin/main` before these edits.
- Next implementation step: file-level audit of reference Android overlay/animation code, then a native Android shell with Mori's main view, chat, and a small state-linked animation set. Keep existing server loopback-only until authenticated HTTPS access is implemented.
- GitHub publishing still needs a credential/account with write access to `breeze-wind/ds_fatfish_town`; the last connected GitHub app account had only pull permission.
- Local commit for this plan: current `HEAD` on `main`. `git diff --check` passed and the changed documentation matched no high-confidence credential pattern. No tests were run because behavior/code did not change. `git push origin main` was attempted and returned `could not read Username` with interaction disabled; local `main` is two commits ahead of `origin/main`.

## Direction update — 2026-11-17

- The user reviewed the prototype and approved a dedicated Cyber Habitat app as the primary phone experience. QQ is now an optional later adapter. Read `docs/product-direction-2026-11-17.md` before planning new work; it supersedes the October QQ-first priority below.
- The user found promising desktop-pet animation material, but has not supplied files or licensing details. Build an animation-state contract and mobile view with placeholders first; inspect the real material before importing it.
- Current source review found only the existing static `habitat.html` UI, server API, SQLite core, and prepared but unverified QQ bridge. No new app code or runtime test was performed in this documentation update.
- Repo sync: `git fetch --all --prune` succeeded on 2026-11-17; local `main` was clean and matched `origin/main` at `b98b648` before editing.
- The direction update was committed locally at the current `HEAD`. Push was attempted, but Git's stored GitHub credential is currently unavailable (`could not read Username` with noninteractive prompt disabled). The connected GitHub app is authenticated as `bding5746-del` and reports read-only access to `breeze-wind/ds_fatfish_town` (`push=false`). Local `main` is one commit ahead of `origin/main`; do not claim this update is on GitHub until the correct account or write access is restored and the remote head is verified.
- Next action: implement the first mobile home view and animation-state binding, then work through authenticated HTTPS phone access and actual device acceptance. Improve Mori's behavior alongside the UI. Ask the user for the desktop-pet asset/link and whether they mean in-app animation or system-level pet overlay.

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
