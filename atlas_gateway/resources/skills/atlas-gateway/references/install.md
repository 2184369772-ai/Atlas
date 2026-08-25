# Atlas Gateway Skill Install

## Current Codex Skill Format Used

- user-level or system-level skill folder
- required `SKILL.md`
- optional `agents/openai.yaml`
- optional `scripts/` and `references/`

This skill is stored in the Atlas repo at `skills/atlas-gateway/`.

## Current Discovery Reality

In the current environment, installed user skills live under:

- `%USERPROFILE%\.codex\skills\`

The repository copy alone is not enough for current user-level discovery. Install or link the skill into the user skill directory.

## Recommended Local Install

From any environment where Atlas is installed:

```powershell
atlas skill install
```

Default behavior:

- copies the bundled skill into the current user-level Codex skill directory
- uses `CODEX_HOME` when set, otherwise the user's `.codex` directory
- does not hardcode a Windows path

## Verify Install

```powershell
atlas skill status
atlas doctor
```

Check:

- the installed skill path exists under `%USERPROFILE%\.codex\skills\atlas-gateway`
- `SKILL.md` is present there
- the runner can resolve the Atlas repository and Gateway entry

## Disable / Uninstall

```powershell
atlas skill uninstall
```

This removes only the installed copied skill folder in the user skill directory. It does not delete the package or repository source.

## Legacy Script Compatibility

The repository still includes the original local script:

```powershell
python skills/atlas-gateway/scripts/install_local.py install
python skills/atlas-gateway/scripts/install_local.py status
python skills/atlas-gateway/scripts/install_local.py uninstall
```

Prefer the `atlas skill ...` commands for public installs.

## Gateway Location

The runner can use either an Atlas source checkout or an installed `atlas_gateway` package. If neither is available, it stops with a clear error.

## Current Real Limitation

This implementation proves the current on-disk format and install path, but it does not prove that an already-running Codex session hot-reloads newly installed skills. A new task or refreshed environment may be required for the skill to appear in future skill selection lists.
