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
