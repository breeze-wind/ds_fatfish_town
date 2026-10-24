# Cyber Habitat DSH bundle

This external DSH bundle registers three tools in a DSH conversation: list residents, read a requested number of recent events, and submit a resident action. It calls the separate Cyber Habitat HTTP service. The World Director remains authoritative and can block an action.

The plugin only accepts an HTTP URL on loopback (`127.0.0.1`, `[::1]`, or `localhost`). The default is `http://127.0.0.1:8765`. The service has no authentication; keep both processes local.

## Install into an isolated DSH profile

From the Cyber Habitat repository root, set a disposable Harness home, then add the Web UI bundle and this plugin to a separate profile:

```powershell
$habitat = (Resolve-Path .).Path
$env:DSH_HOME = Join-Path $habitat 'work\dsh-cyber-habitat-profile-test'
Push-Location 'E:\deepseek-harness'
pnpm dsh plugin --profile web add "$habitat\integrations\dsh-plugin"
pnpm dsh web --dump-config
pnpm dsh web
Pop-Location
```

Start the Cyber Habitat service first. Then open the local Web UI from the DSH terminal output and ask the agent to list residents, inspect recent events, or submit an action. `attack` is an intentional example: it reaches the director and is denied there. The `web` profile and package install are isolated under this repository's ignored `work/` directory; the desktop application's existing profile is untouched. The plugin declares DSH APIs as peers so it uses the Harness installation's matching tool registry and schema validator.

This is an MVP agent-tool integration, not a dedicated dashboard. It does not patch the DSH source tree or access the desktop application's existing profile. Review `E:\deepseek-harness\AGENTS.md` and the DSH plugin docs before any DSH source changes.
