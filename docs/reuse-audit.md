# Reuse audit (Sprint 0)

Initial bounded search did not inspect the separate `E:\` development drive, so its earlier conclusion that no DSH source/install was found was incomplete. Follow-up inspection found the user's existing source checkout at `E:\deepseek-harness` and packaged desktop app at `E:\dsh\DeepSeek Harness.exe`. No new source download is needed.

The user's clarification is that their DSH is the desktop GUI. The local checkout is the upstream `deepseek-ai/deepseek-harness` repository on branch `master`, at commit `d347e703908d0406b7a7ef80e3a0e594d86b2215`; its build metadata records client version `0.1.3-alpha.1`. The repository includes `node_modules` and `.dsh-build`. A packaged Windows app exists under `E:\dsh`. The upstream README states MIT licensing and developer-preview status.

Official DSH Desktop documentation describes that app as a Windows/macOS shell that manages the local Harness service; the agent, web UI, and plugin core come from the pinned Harness upstream. DSH's own plugin documentation supports installable bundles and profile composition. Thus a future integration could be a separate DSH plugin/UI that calls a Cyber Habitat service. The desktop shell is not a world simulation runtime, and this repository does not document a `RuntimePort`-compatible resident-action API.

Attempts to download duplicate source during this task were interrupted or failed during transfer. They were unnecessary because the existing checkout was found. No source files were modified, no install/build was run, and no server was accessed. Git status could not be read through the current filesystem boundary, so whether the existing checkout has local edits is unverified. Preserve and use the existing checkout in place; do not copy the large repository into Cyber Habitat's `vendor/` directory.

Sprint 2 validation used the existing checkout without editing it: the local bundle was linked into a disposable `DSH_HOME` under Cyber Habitat `work/`, config composition listed the bundle, and the DSH web process reached its local startup URL without plugin schema/load errors. The process was stopped after startup. An actual LLM tool invocation was not attempted because no model account was configured in this isolated profile.

This is a bounded local check, not proof that no DSH files exist elsewhere on the machine. No files were installed, changed, or removed outside the new project. No credentials, private keys, or server configuration were read.

## Reuse decision

- Use Python's `sqlite3`, `dataclasses`, `enum`, and `random` from the standard library.
- Provide `RuntimePort` and a deterministic `MockRuntime` now.
- Use the separate bundle under `integrations/dsh-plugin/` to expose query/action tools in DSH conversations. Keep world state and action policy in Cyber Habitat; do not model a made-up DSH resident-action API. Desktop plugins extend Harness UI/workflows; they do not make the desktop shell a headless simulation engine.
- Revisit existing open-source components after the DSH identity is confirmed; avoid pulling packages into the first offline loop.

## Coopanion desktop-pet reference — 2026-11-17

User-provided official site: <https://coo.palailab.org/>. Public source: <https://github.com/Pal-AI-Lab/Coopanion>. The official guide describes a Windows/macOS/Linux desktop companion that sits at the bottom of the screen, speaks through bubbles, accepts text/voice/touch, and may operate the computer when enabled. The linked Bilibili tutorial could not be viewed through the available web reader; the findings here come from the official site, repository, development guide, and notices, not from watching the video.

### Implementation actually inspected

- `packages/cortico-world-desktop-pet/` is the desktop pet World; `app/` is the Electron host. The [development guide](https://github.com/Pal-AI-Lab/Coopanion/blob/main/docs/DEVELOPMENT.md) describes Cortico Core, Cormini Persona, and the World as separate pieces.
- The [World README](https://github.com/Pal-AI-Lab/Coopanion/blob/main/packages/cortico-world-desktop-pet/README.md) describes a transparent frameless desktop window, speech and option bubbles, touch and drag events, figure packs, movement, and a vocabulary of actions. These are useful interaction patterns for a vivid resident.
- The whale's [`figure.js`](https://github.com/Pal-AI-Lab/Coopanion/blob/main/packages/cortico-world-desktop-pet/web/whale/figure.js) describes a canvas rig with mesh deformation, face texture, and springs for hair, skirt, tail, fins, and ahoge; [`figure.json`](https://github.com/Pal-AI-Lab/Coopanion/blob/main/packages/cortico-world-desktop-pet/web/whale/figure.json) declares the figure pack. This is an animated part rig, not a stack of GIFs or a Cubism SDK model.
- [`electron-builder.yml`](https://github.com/Pal-AI-Lab/Coopanion/blob/main/electron-builder.yml) builds Windows installers/portable ZIPs, macOS DMGs/ZIPs, and Linux AppImage/deb; `asar: false`. Since the preferred source exists and packaged files are not hidden in ASAR, installer unpacking adds little value to the design audit. No binary was downloaded, installed, or unpacked in this review.

### License and reuse boundary

- Current Coopanion source is [AGPL-3.0-or-later](https://github.com/Pal-AI-Lab/Coopanion/blob/main/LICENSE), with an additional Steamworks permission. Its README says releases through 0.1.10 were MIT and Cortico is MIT; do not apply that historical MIT label to current source without checking the exact tag and files.
- The project's [third-party notices](https://github.com/Pal-AI-Lab/Coopanion/blob/main/packages/cortico-world-desktop-pet/THIRD_PARTY_NOTICES.md) explicitly exclude `web/whale/` textures from the AGPL grant. The whale uses a referenced character design and vendor logos. Do not copy these textures, thumbnails, voice assets, or logos into Cyber Habitat based on the code license.
- Technical feasibility: we can study the behavior and independently implement Android-native overlay/input plus our own animation assets. Copying current renderer or World code would require an explicit AGPL compatibility and distribution plan. Coopanion is a desktop Electron product; it is not a drop-in Android APK or replacement for our server.

Decision for the current Android milestone: use Coopanion as a behavior and rig architecture reference. First map interactions to Mori's real chat/state events and create original or clearly licensed art. Defer any direct code import until a file-level license audit and a deliberate repository license decision.
