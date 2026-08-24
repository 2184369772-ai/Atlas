---
name: atlas-gateway
description: "Inspect software projects for Atlas reuse opportunities, interpret Atlas Gateway recommendations, and route to existing Atlas capabilities without upgrading maturity or forcing reuse."
---

# Atlas Gateway

Use this skill when working in a software project and you need to decide whether Atlas has a reusable capability worth checking.

Do not use this skill just because Atlas exists. `NO_ATLAS_REUSE` is a valid and preferred outcome when Atlas is not a good fit.

## What Atlas Is

Atlas is a governance-first repository of reusable software capabilities.

Atlas Skill v0.1 does not reimplement Atlas. It routes through Atlas Gateway so runtime capability facts stay in one place.

## First Action in a New Project

For a new or unfamiliar software project, first inspect the project through Gateway:

```powershell
python scripts/run_gateway.py project inspect <project-path> --json
```

Use that result before recommending Atlas.

## Gateway Commands

Use the runner script in this skill so Atlas can be located safely:

```powershell
python scripts/run_gateway.py capability list
python scripts/run_gateway.py capability show tabular-core
python scripts/run_gateway.py project inspect <project-path> --json
python scripts/run_gateway.py file inspect <file>
python scripts/run_gateway.py context --output ATLAS_CONTEXT.md
```

If the runner cannot find Atlas Gateway, stop and report the missing location clearly. Do not guess maturity from stale skill text.

## Recommendation Mapping

### `CONTROLLED_REUSE`

- Atlas has a narrowly governed reuse path.
- You may suggest the capability, call Gateway, and help the project build its own adapter.
- Keep business rules, sheet selection, field mapping, validation, `ImportBatch`, ORM/JDBC, and database writes in the project.

### `REFERENCE_ONLY`

- Atlas has a Candidate, not a stable package promise.
- You may inspect capability details and reuse the boundary or contract ideas.
- Do not claim Atlas already provides a mature callable implementation.
- Do not force the project to depend on Atlas.

### `SEMANTIC_REFERENCE`

- Only the language and boundary are reusable.
- If there is no package, do not pretend there is a callable implementation.

### `INBOX_ONLY`

- Candidate Inbox is not a Candidate capability.
- You may reference the pattern and boundary only.
- Do not create project dependencies or present it as implemented Atlas functionality.

### `NO_ATLAS_REUSE`

- Accept it and continue normal project work.
- Do not add Atlas-specific layers just to force reuse.

## File Handling Boundary

When Gateway recommends Tabular reuse for CSV/XLSX understanding, call:

```powershell
python scripts/run_gateway.py file inspect <file>
```

Atlas only owns general tabular structure and value semantics. The project keeps:

- business sheet selection
- business field mapping
- required business fields
- default business values
- business validation
- workflow and import batch logic
- ORM/JDBC and database writes

## Capability Facts Source

If you are unsure about Atlas maturity or allowed usage, query Gateway first:

- `python scripts/run_gateway.py capability list`
- `python scripts/run_gateway.py capability show <capability>`

Gateway and the capability catalog are the runtime fact source. This skill text is behavior guidance, not the source of truth for current maturity.

## Context Pack

When another AI or GPT needs a short Atlas context, generate it through Gateway:

```powershell
python scripts/run_gateway.py context --output ATLAS_CONTEXT.md
```

Keep the result public-safe.

## Public-Safe Rule

Do not include or forward:

- company business details
- internal evidence details
- ignored review artifacts
- private absolute machine paths
- private provenance or secrets

## References

- For installation, enable/disable, and verification, read [references/install.md](references/install.md).
- For the expected project-routing behavior and validation scenarios, read [references/usage.md](references/usage.md).
