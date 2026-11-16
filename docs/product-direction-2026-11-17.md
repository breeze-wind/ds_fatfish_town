# Product direction: a living resident in a dedicated app

Date: 2026-11-17. This records the user's direction after reviewing the October prototype. It supersedes the earlier priority to finish the QQ bridge first. It does not claim the app or animations already exist.

> Later on 2026-11-17 the user clarified that routine autonomous activity can wait. The current priority is a lively, human-like desk pet and chatbot with a beautiful interface. See `android-pet-plan.md` for the canonical plan; the autonomy and PWA-first goals below are retained as historical context.

## What the user has confirmed

- Cyber Habitat should feel like a persistent world with an AI resident who makes most ordinary decisions independently. Complete the first resident before adding many residents.
- The phone must be a practical way to visit and talk with that same resident. The user now prefers a dedicated Cyber Habitat app as the main experience over QQ integration.
- The user has found appealing desktop-pet animation material and sees strong potential in animated presentation. No asset files, license, format, target platform, or use permission have yet been supplied or verified.
- DeepSeek direct API is approved under the existing bounded-data-flow arrangement. DSH is optional. The world remains server-backed and uses the existing action policy and persistent store.

## Experience to build

The home view should make the resident's present activity, location, intention, and state understandable at a glance. The resident may be animated, but animations must correspond to real states such as resting, exploring, creating, listening, and speaking. A transition should be driven by a recorded world decision or interaction; a looping sprite must not imply actions that did not happen. A compact timeline should explain what changed in the world. Chat should feel like visiting the resident, not operating a control panel. The resident should resume their own life after an interaction.

The first delivery target is an installable, mobile-first web app using the existing backend. This is an implementation choice for quick validation, not a decision that native Android is permanently excluded. Mobile access requires authenticated HTTPS and server-side model secrets before it can be exposed beyond loopback. The existing unauthenticated port 8765 must not simply be opened to the internet.

## Next vertical slice and acceptance

1. Design the resident home view for a narrow phone screen: animated resident area, current activity and intention, one conversation entry point, and a readable recent-life timeline.
2. Define an animation-state contract keyed to persisted resident/world state. Include an idle/unknown fallback and reduced-motion option. Use placeholder art until the user's chosen asset and rights are inspected.
3. Make the view load from the existing resident and event APIs, with a clear distinction between observed action, current intention, and generated speech.
4. Add a web app manifest and installable shell. Verify home-screen launch and state persistence on a real phone only when a safe access route is ready.
5. Improve resident decision quality in parallel: cooldowns, useful world effects, memory continuity, and event cadence. Judge the app with these behaviors, not just with screenshots.

Acceptance for the first local slice: a phone-sized browser can show Mori's current activity and recent changes, chat with him through the same stored conversation, and display an animation state justified by stored data. No invented activity, repeated placeholder events, or unbounded model calls. Secure phone-to-server access and actual installability remain separate acceptance gates until verified on a device.

## Still to learn from the user

- Whether “desktop pet” means visual assets inside the app, an Android home-screen widget/overlay, a Windows desktop companion, or more than one of these.
- The asset source, license, file format, animation states, resolution, and whether derivative work and redistribution are allowed.
- The desired resident appearance, world art style, interaction rhythm, and whether the resident may initiate notifications.
- Whether the separate Android DSH/device-control experiment should eventually connect to this resident. Prior discussion explored it, but it is not a confirmed app requirement.

## Existing implementation boundary

As of the last verified October source snapshot, the UI is one static HTML page. The backend has DeepSeek chat, an opt-in scheduler, action validation, and SQLite persistence. The QQ bridge has preparation code and a test container but no verified phone message round trip. There is no app shell, animation system, account login, HTTPS remote access, or installed mobile acceptance yet.
