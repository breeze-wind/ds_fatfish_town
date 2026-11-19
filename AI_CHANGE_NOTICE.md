# AI Change Notice

This is the required special notice file for changes that replace, substantially rewrite, or take ownership of code created by another AI. Every later AI must read this file before editing shared code.

When applicable, append one entry per change. Do not erase or rewrite prior entries. Use file paths and commit IDs so the original owner and next agent can trace the change. If authorship is unclear, say `unknown`; do not invent an owner.

## Entry format

### YYYY-MM-DD — short change name

- Previous owner/source:
- Changed files:
- Why this changed:
- Behavior/API/data effects:
- Compatibility or migration notes:
- Validation performed and result:
- Original owner notified / next owner:
- Commit:

## Change ledger

Documentation updates and ordinary additive work should still be listed in `AI_HANDOFF.md`; add a ledger entry here whenever another AI's code is modified or superseded.

### 2026-11-17 — Mori browser home and chat guidance

- Previous owner/source: `unknown`; earlier agents wrote `src/cyber_habitat/habitat.html` and `src/cyber_habitat/ai.py`.
- Changed files: `src/cyber_habitat/habitat.html`, `src/cyber_habitat/ai.py`.
- Why this changed: user prioritized a vivid desk pet and chat over the world administration dashboard and repetitive autonomous activity.
- Behavior/API/data effects: mobile browser home now shows Mori, stored dialogue, real resident state, and interaction-linked animation; prompt guidance discourages repeated filler and claims of unrecorded activity. DeepSeek non-thinking chat temperature changes to 1.3; JSON actions stay at 0.7. No HTTP or SQLite schema change.
- Compatibility or migration notes: world/admin controls remain in expandable settings; no data migration. The original inline SVG is project-authored placeholder art, not third-party pet assets.
- Validation performed and result: 390×844 browser inspection; simulated UI message and page reload with a fake model and temporary SQLite database passed; Python suite result is recorded in `AI_HANDOFF.md`.
- Original owner notified / next owner: original owner unknown; next AI should read this ledger and continue native Android client and secure access.
- Commit: `e25884a` for the changed code and initial notice; follow-up handoff commit records the exact delivery state.

### 2026-11-17 — Ground Mori's activity replies in recorded actions

- Previous owner/source: `unknown` for the original service, store, and prompt code; the previous prompt edit was `e25884a` by this AI.
- Changed files: `src/cyber_habitat/ai.py`, `src/cyber_habitat/service.py`, `src/cyber_habitat/store.py`, and corresponding tests.
- Why this changed: real DeepSeek turns still invented unrecorded locations and actions and handled repeated activity questions mechanically.
- Behavior/API/data effects: chat prompt now includes only this resident's approved past actions and explicit absence of real-time world activity; repeated activity questions receive turn-specific grounding and anti-repetition guidance. No HTTP or SQLite schema change. The new store query is read-only.
- Compatibility or migration notes: no migration; old model-written chat remains in history as utterances, not verified world facts.
- Validation performed and result: 32 Python tests passed. Nine real-model calls on temporary test residents informed the revision; final three-turn sample avoided unrecorded physical actions and repeated question endings, but broader quality acceptance is still pending.
- Original owner notified / next owner: original owner unknown; next AI should read this ledger, compare multiple live runs, and obtain user feedback on tone.
- Commit: `c606b36` for the grounded-dialogue code and initial notice; follow-up handoff commit records final delivery status.

### 2026-11-17 — Add explicit saved resident memory

- Previous owner/source: `unknown` for the original store, service, browser UI, and prompt code; this AI made the preceding dialogue edits.
- Changed files: `src/cyber_habitat/store.py`, `src/cyber_habitat/service.py`, `src/cyber_habitat/ai.py`, `src/cyber_habitat/habitat.html`, tests, and API/product docs.
- Why this changed: the resident forgot important facts once they left the 12-message context window; inferred memory risked turning guesses into facts.
- Behavior/API/data effects: schema v4 adds user-saved resident memories; GET/POST/DELETE memory routes expose explicit add/list/remove, capped at 20 notes of 240 characters. Saved notes join future chat prompts only; memory events contain IDs, not note text. The UI discloses model sharing and that deletion does not erase original chat.
- Compatibility or migration notes: v1–v3 SQLite databases migrate to v4 on startup; no key or external data is moved. Delete is not secure erasure of old chat or provider copies.
- Validation performed and result: Python tests and browser UI smoke-test results are in the current `AI_HANDOFF.md`.
- Original owner notified / next owner: original owner unknown; next AI should implement edit/correction and provenance-aware candidate memories only after user feedback.
- Commit: `e6fabb4` for the saved-memory code and initial notice; follow-up handoff commit records final delivery status.

### 2026-11-18 — Add direct editing for saved resident memories

- Previous owner/source: `unknown` for the original SQLite store, HTTP memory routes, and browser memory panel; latest prior code milestone was `e6fabb4`.
- Changed files: `src/cyber_habitat/store.py`, `src/cyber_habitat/service.py`, `src/cyber_habitat/habitat.html`, `docs/service-api.md`, `README.md`, and `AI_HANDOFF.md`.
- Why this changed: users need to correct a saved fact in place when it becomes outdated or was phrased incorrectly.
- Behavior/API/data effects: adds `PUT /residents/{id}/memories/{memory_id}` with the existing 1–240 character validation; duplicate text returns `409`, missing memory returns `404`, and an unchanged value creates no event. Changed content creates `resident.memory_updated` with only the note ID; original `created_at` remains unchanged. The UI provides inline edit/save/cancel controls. No schema migration.
- Compatibility or migration notes: additive HTTP endpoint; existing SQLite data remains compatible. Future chats use the corrected text; prior chat messages and model-provider copies are not changed.
- Validation performed and result: `git diff --check` passed and the loopback service restarted with `/healthz` returning `ok`; the new edit/duplicate/delete flow was not yet exercised. No tests were added or run.
- Original owner notified / next owner: original owner unknown; next AI should perform the synthetic end-to-end flow after confirming the in-app browser/host networking path. Do not expose unauthenticated port 8765 beyond loopback.
- Commit: `e7f844c`.

### Whale-girl Mori browser redesign

- Previous owner/source: browser home from `e25884a`, memory controls from `e7f844c`, HTTP service owner unknown.
- Changed paths: `src/cyber_habitat/habitat.html`, `service.py`, `mori.webp` and package data. The user asked to replace the giant whale with a whale girl and look for a reusable open source UI.
- Effects: dashboard cards became a character stage and conversation panel. Existing element hooks for chat, memory and world controls are retained. Added a static illustration endpoint. No database migration.
- Attribution and delivery status are in `THIRD_PARTY_NOTICES.md` and `AI_HANDOFF.md`.

### 2026-11-19 — Play community whale-girl loops in the Mori preview

- Previous owner/source: Mori browser redesign in `d30b6dd`; earlier service and interaction code by prior project agents.
- Changed files: `src/cyber_habitat/habitat.html`, `src/cyber_habitat/service.py`; added `scripts/fetch_whale_preview.py` and attribution.
- Why this changed: user asked to try the community 大肥鱼 appearance after reviewing the generated illustration.
- Behavior/API/data effects: add four allowlisted loopback media paths; original illustration remains available. This changes the browser presentation only; no model, database or World Director changes.
- Compatibility or migration notes: original illustration is the fallback. The assets are optional, local and separately licensed.
- Validation performed and result: four transparent clips downloaded; local HTTP and Edge playback checks passed; see `AI_HANDOFF.md`.
- Original owner notified / next owner: next UI/Android agent should preserve attribution and avoid including noncommercial assets in production builds.
- Commit: `Preview the community whale-girl animations in Mori` (the commit containing this entry).
