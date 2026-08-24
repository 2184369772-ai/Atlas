# Atlas

Atlas is an experimental development framework that helps AI and Codex discover, judge, and carefully reuse validated engineering capabilities in software projects.

Atlas is not:

- a universal AI coding agent
- a platform that automatically generates enterprise systems
- a Workflow/Auth/RBAC framework
- a system that automatically learns your codebase

Current public package version: `0.1.0-alpha`

License: `Apache-2.0`

## Quick Start

1. Clone this public distribution into a new directory.
2. Create and activate a virtual environment:

```bash
python -m venv .venv
```

3. Install Atlas in editable mode:

```bash
pip install -e .
```

4. Inspect current Atlas capabilities:

```bash
atlas capability list
atlas capability show tabular-core
```

5. Inspect your current project:

```bash
atlas project inspect .
```

6. Generate a public-safe context pack:

```bash
atlas context
```

## Current Capabilities

- Tabular Core: `CONTROLLED_REUSE`
- Runtime Config: `REFERENCE_ONLY`
- File Lifecycle: `REFERENCE_ONLY`
- Operation Outcome: `SEMANTIC_REFERENCE`

Current maturity note:

- Tabular Core is the current most mature public Atlas capability.
- Runtime Config and File Lifecycle remain reference-only Candidates.
- Operation Outcome remains a semantic reference, not a shipped package.
- Atlas does not automatically learn project code.
- `NO_ATLAS_REUSE` is a normal outcome when Atlas is not a fit.

## Codex Skill

If you use Codex, Atlas also ships a local skill:

```bash
python skills/atlas-gateway/scripts/install_local.py install
```

Then verify the install:

```bash
python skills/atlas-gateway/scripts/install_local.py status
python skills/atlas-gateway/scripts/run_gateway.py --status
```

Current real limitation:

- install the skill before expecting Codex to use it
- a new task or new session is more reliable than expecting hot reload
- Atlas is not triggered for every task
- `NO_ATLAS_REUSE` is a valid result

## Commands

- `atlas capability list`
- `atlas capability show tabular-core`
- `atlas project inspect <project-path>`
- `atlas file inspect <file>`
- `atlas context`
- `python -m atlas_gateway ...`

## Packaging Note

If you create a real public GitHub repository from this package, initialize a brand-new Git repository from this exported directory only.

Do not push the Git history of an internal training or development repository.
