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

If Atlas may help, build the adoption plan next. When the user has provided a
specific current task, pass it to task-aware routing:

```powershell
python scripts/run_gateway.py project plan <project-path> --json
python scripts/run_gateway.py project plan <project-path> --task "<current task>" --json
```

Use these results before recommending Atlas. If Gateway returns
`PROJECT_RELEVANT`, the project may contain Atlas-relevant patterns but the
current task should continue without Atlas adoption. If Gateway returns
`NO_ATLAS_REUSE`, continue normal project work without adding Atlas-specific
layers.

## Gateway Commands

Use the runner script in this skill so Atlas can be located safely:

```powershell
python scripts/run_gateway.py capability list
python scripts/run_gateway.py capability show tabular-core
python scripts/run_gateway.py project inspect <project-path> --json
python scripts/run_gateway.py project plan <project-path> --json
python scripts/run_gateway.py project plan <project-path> --task "<current task>" --json
python scripts/run_gateway.py adapter init enterprise-intake --target <project-path>
python scripts/run_gateway.py adapter init ai-execution --target <project-path>
python scripts/run_gateway.py adapter init knowledge-intake --target <project-path>
python scripts/run_gateway.py doctor
python scripts/run_gateway.py file inspect <file>
python scripts/run_gateway.py ui review <project-path> --json
python scripts/run_gateway.py ui fix <project-path> --dry-run --json
python scripts/run_gateway.py context --output ATLAS_CONTEXT.md
```

For user-facing shell examples, `atlas ...` is preferred after package installation. Inside the Skill, prefer `python scripts/run_gateway.py ...` because it can locate an Atlas source checkout or installed package without requiring the user's project shell to have `atlas` on PATH.

If the runner is unavailable but `atlas` is installed, the CLI is an acceptable fallback:

```powershell
atlas doctor
```

If neither command can find Atlas Gateway, stop and report the missing location clearly. Do not guess maturity from stale skill text.

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

### Task-Level Decisions

When `project plan --task` is used, interpret task-level decisions separately
from project-level findings:

- `TASK_REUSE`: the current task explicitly needs a controlled Atlas package,
  API, adapter, or bridge.
- `TASK_REFERENCE`: the current task can use Atlas contract or semantic
  boundaries as reference, but implementation remains project-owned.
- `PROJECT_RELEVANT`: Atlas may be relevant to the project overall, but the
  current task should not adopt it.
- `NO_ATLAS_REUSE`: neither the project nor the current task has useful Atlas
  reuse.

Do not recommend Atlas merely because the repository contains Excel files,
runtime config, file uploads, reports, or existing import code. For local bug
fixes, compatibility fixes, approval-page work, or UI/page routing tasks, prefer
`PROJECT_RELEVANT` or `NO_ATLAS_REUSE` unless the task explicitly needs Atlas
semantics.

## Adoption Kit Boundary

Default workflow for a new project:

```text
project inspect
-> project plan
-> adapter init only when the task explicitly requires Atlas adoption
-> normal project development
```

Do not automatically write scaffold files into a user project. Use `adapter init` only when the user request or task scope clearly asks to connect Atlas.

## UI Closeout Workflow

When a project has real frontend/UI code and the current task reaches function
complete, phase acceptance, or UI closeout, use Gateway to suggest the UI
closeout loop:

```text
function complete
-> ui review
-> safe-fix dry-run
-> apply safe items only with explicit authorization
-> visual recommendations
-> Codex optimization
-> human final aesthetic confirmation
```

Run the review commands through the skill runner:

```powershell
python scripts/run_gateway.py ui review <project-path> --json
python scripts/run_gateway.py ui fix <project-path> --dry-run --json
```

Do not require every project to run UI review. If Gateway returns
`NO_ATLAS_REUSE`, continue normal project work. If the project has no real
frontend/UI code, do not suggest UI Quality.

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

## UI Review Boundary

When Gateway recommends UI Quality & Interaction Reliability, call:

```powershell
python scripts/run_gateway.py ui review <project-path> --json
python scripts/run_gateway.py ui fix <project-path> --dry-run --json
```

Treat the result as a review checklist. Atlas can report basic page and
interaction reliability risks, but the project keeps brand style, business copy,
visual taste, workflow, and final design judgement.

Visual recommendations include evidence, confidence, and an execution mode.
Codex may apply `codex_edit` recommendations only after checking the actual page
context. `human_judgment` and `BUSINESS_JUDGMENT` items require the user or
product owner. Never route a visual recommendation into `ui fix --safe`.

`ui fix` is dry-run unless `--safe` is explicit. Apply `--safe` only when the
user authorized project edits. It may perform high-confidence mechanical fixes,
but destructive actions, state copy, visual hierarchy, spacing, density,
grouping, and complex layout stay under human review.

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
