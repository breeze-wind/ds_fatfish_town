# Architecture decision: local core, adapters at the edge

Status: accepted for Sprint 0.

## Context

The world needs a central decision point that can eventually consult AI, constrain harmful actions, and add occasional unscripted events. An existing DeepSeek Harness source checkout and packaged DSH desktop app are present on the separate `E:` drive. The DSH Desktop GUI is a shell around the Harness service; it is not itself a simulation engine. Docker is not available in the current shell, and WSL status returned access denied.

## Decision

Use a Python standard-library domain core. A `Resident` submits an `Action` to `WorldDirector`; the director applies hard rules, chooses optional seeded random events, asks a `RuntimePort` to apply an allowed effect, and records outcomes with `EventStore`. The mock runtime provides the first end-to-end loop. If DSH integration is wanted, review its actual bundle/profile plugin model and connect a DSH plugin/UI to a Cyber Habitat service; do not assume DSH implements the runtime port.

AI integration, when added, returns proposals to the director. It cannot mutate residents or write around policy checks. Randomness is injected as a seedable generator so tests and reproductions are reliable.

## Consequences

- Sprint 0 runs offline on Windows and does not need Docker/WSL.
- Simulation rules and persistence are testable without a real DSH runtime.
- DSH plugin communication, identity mapping, and lifecycle semantics remain open until the intended UI/service flow is designed against the local source checkout.
- SQLite is suitable for a single-process prototype, not a claim of multi-writer production readiness.
- Compose and Dockerfile are preparation artifacts only; this sprint does not build or deploy them.
