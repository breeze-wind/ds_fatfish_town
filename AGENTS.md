# Repository guidance

- Keep the core local-first and standard-library-only until a concrete need justifies dependencies.
- Route every resident action through `WorldDirector`; runtimes must not bypass policy checks.
- Persist state-changing outcomes as immutable SQLite events.
- Keep DSH integration behind `RuntimePort`; do not invent endpoints or assume an installed product without verifying it.
- Treat AI output as an untrusted proposal. The deterministic director validates it before execution.
- Do not add credentials, private keys, production URLs, or real resident personal data.
- Tests use only temporary databases and deterministic seeds.
