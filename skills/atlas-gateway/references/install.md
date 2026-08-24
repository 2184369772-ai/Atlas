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

From the Atlas repo root:

```powershell
python skills/atlas-gateway/scripts/install_local.py install
```

Default behavior:

- creates a junction at `%USERPROFILE%\.codex\skills\atlas-gateway`
- points it to the repository skill source
- preserves a portable repo-owned source of truth

## Verify Install

```powershell
python skills/atlas-gateway/scripts/install_local.py status
python skills/atlas-gateway/scripts/run_gateway.py --status
```

Check:

- the installed skill path exists under `%USERPROFILE%\.codex\skills\atlas-gateway`
- `SKILL.md` is present there
- the runner can resolve the Atlas repository and Gateway entry

## Disable / Uninstall

```powershell
python skills/atlas-gateway/scripts/install_local.py uninstall
```

This removes only the installed junction or copied folder in the user skill directory. It does not delete the repository source.

## If You Install by Copy Instead of Junction

The runner can still find Atlas through:

1. `ATLAS_REPO_ROOT`
2. current working directory upward search
3. the script path upward search

If none of those work, the runner stops with a clear error.

## Current Real Limitation

This implementation proves the current on-disk format and install path, but it does not prove that an already-running Codex session hot-reloads newly installed skills. A new task or refreshed environment may be required for the skill to appear in future skill selection lists.
