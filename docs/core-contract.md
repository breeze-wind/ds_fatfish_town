# Core interface contract

## Domain

- `Resident`: stable id, display name, and bounded integer needs (`energy`, `safety`, `growth`), each 0–100.
- `Action`: resident id, action kind, and optional short detail.
- `Decision`: `allowed` or `blocked`, reason, and event id.
- `WorldEvent`: append-only id, UTC timestamp, type, subject, JSON payload.

## Flow

1. `WorldDirector.submit(resident, action)` validates that the action targets that resident and matches the action vocabulary.
2. Hard safety rules reject dangerous actions before the runtime is called.
3. The runtime applies an allowed effect and returns the updated resident.
4. The director records the outcome and may record one scheduled random event according to injected probability/RNG.
5. The caller receives a decision plus emitted events; failures do not silently report success.

## Ports

- `RuntimePort.apply(resident, action) -> Resident`: runtime effect boundary.
- `EventStore.append(type, subject, payload) -> WorldEvent`: durable event boundary.
- AI, future: proposes `Action`/event candidates only. The director remains authoritative.
- DSH, future: implements `RuntimePort` only after the actual DSH contract is verified.

## Sprint 0 allowed action kinds

`rest`, `learn`, `socialize`, `attack`. `attack` is deliberately blocked to demonstrate a safety invariant. Unknown action kinds are rejected as invalid input and are not sent to a runtime.
