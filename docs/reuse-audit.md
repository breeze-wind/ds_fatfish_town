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
