# Architecture decision: local core, adapters at the edge

Status: accepted for Sprint 0.

## Context

The world needs a central decision point that can eventually consult AI, constrain harmful actions, and add occasional unscripted events. An existing DeepSeek Harness source checkout and packaged DSH desktop app are present on the separate `E:` drive. The DSH Desktop GUI is a shell around the Harness service; it is not itself a simulation engine. Docker is not available in the current shell, and WSL status returned access denied.

## Decision

Use a Python standard-library domain core. A `Resident` submits an `Action` to `WorldDirector`; the director applies hard rules, chooses optional seeded random events, asks a `RuntimePort` to apply an allowed effect, and records outcomes with `EventStore`. The mock runtime provides the first end-to-end loop. DSH integration is a separate bundle whose tools call the local HTTP service; DSH does not implement the simulation runtime port.

AI integration, when added, returns proposals to the director. It cannot mutate residents or write around policy checks. Randomness is injected as a seedable generator so tests and reproductions are reliable.

## Consequences

- Sprint 0 runs offline on Windows and does not need Docker/WSL.
- Simulation rules and persistence are testable without a real DSH runtime.
- The DSH bundle installs and loads in an isolated local profile. Model-driven calls, identity mapping, and dedicated dashboard UI remain later work.
- SQLite is suitable for a single-process prototype, not a claim of multi-writer production readiness.
- Compose and Dockerfile are preparation artifacts only; this sprint does not build or deploy them.
