# Repository guidance

- Keep the core local-first and standard-library-only until a concrete need justifies dependencies.
- Route every resident action through `WorldDirector`; runtimes must not bypass policy checks.
- Persist state-changing outcomes as immutable SQLite events.
- Keep DSH integration behind `RuntimePort`; do not invent endpoints or assume an installed product without verifying it.
- Treat AI output as an untrusted proposal. The deterministic director validates it before execution.
- Do not add credentials, private keys, production URLs, or real resident personal data.
- Tests use only temporary databases and deterministic seeds.

## Mandatory handoff and shared-work rules

- At the start of every task, read `README.md`, this file, `AI_HANDOFF.md`, and `AI_CHANGE_NOTICE.md`; then inspect the working tree before making changes.
- Always attempt `git fetch --all --prune` before coding. If the correct remote branch exists, fast-forward a clean branch or attempt to merge the latest commits without discarding local work. Never use `reset --hard`, force-push, or overwrite an unowned change to make sync easier.
- If separate agents are working concurrently, use separate branches/worktrees and agree on file/API ownership. Do not concurrently edit shared core files without coordination.
- Resolve ordinary implementation differences yourself using the accepted architecture and user requirements. Record decisions that affect contracts or future work. Ask the user only when the decision changes product direction, data sharing, account identity/access, costs, public exposure, production systems, or cannot be resolved from existing requirements.
- When changing code originally authored or owned by another AI, append a dated entry to `AI_CHANGE_NOTICE.md` before finishing. Identify the previous owner/source, changed paths, why the change was necessary, behavior/API effects, validation, and follow-up owner. Do not silently replace another agent's work.
- Every completed work unit must leave `AI_HANDOFF.md` updated with exact status, files, commit, commands/tests and results, deployment state, remaining blockers, and the next concrete action. A plan without completed work is not a handoff.
- Commit meaningful completed slices. Attempt to push to the user's intended GitHub repository after each milestone, but first verify the authenticated owner and remote. Never publish to a similarly named or wrong account. If the correct GitHub remote/account is unavailable, keep the local commit and state exactly what the account holder must reconnect.
- Before a commit or push, check the diff, generated files, Git history, `.env`/token/QQ data, and logs for secrets. Do not include live credentials, QQ account identifiers, chat logs, or production data in the repository.
- Report only evidence actually obtained. A container starting, an endpoint returning 200, or a plugin loading does not prove QQ round-trip, user-level acceptance, or production readiness.
