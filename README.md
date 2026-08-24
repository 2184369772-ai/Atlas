# Atlas

Atlas is an experimental development framework that helps AI and Codex discover, judge, and carefully reuse validated engineering capabilities in software projects.

Atlas is not:

- a universal AI coding agent
- a platform that automatically generates enterprise systems
- a Workflow/Auth/RBAC framework
- a system that automatically learns your codebase

Current public package version: `0.4.0-alpha`

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
atlas capability show enterprise-intake
atlas capability show ai-execution
atlas capability show knowledge-intake
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
- Enterprise Intake: `REFERENCE_ONLY`
- AI Execution: `REFERENCE_ONLY`
- Knowledge Intake: `REFERENCE_ONLY`
- Runtime Config: `REFERENCE_ONLY`
- File Lifecycle: `REFERENCE_ONLY`
- Operation Outcome: `SEMANTIC_REFERENCE`

Current maturity note:

- Tabular Core is the current most mature public Atlas capability.
- Enterprise Intake is a shadow-validated Candidate, not a Stable Module.
- AI Execution is a shadow-validated Candidate, not a Stable Module.
- Knowledge Intake is a shadow-validated Candidate, not a Stable Module.
- Runtime Config and File Lifecycle remain reference-only Candidates.
- Operation Outcome remains a semantic reference, not a shipped package.
- Enterprise Intake still requires a project-side adapter for duplicate policy, business validation, persistence, transactions, and DB writes.
- AI Execution still requires a project-side provider adapter for provider calls, prompts, model choice, RAG/Knowledge, retry/timeout behavior, business rules, and persistence.
- Knowledge Intake still requires a project-side adapter for OCR/parsing, chunking, embedding/vector DB, retrieval/ranking strategy, prompts/LLMs, business knowledge, persistence, and permissions.
- Atlas does not automatically learn project code.
- `NO_ATLAS_REUSE` is a normal outcome when Atlas is not a fit.

## Enterprise Intake Example

Run the public-safe synthetic example:

```bash
python examples/enterprise-intake-synthetic/run_example.py
```

This example proves:

- Tabular input
- project adapter
- preview
- row decision and issues
- commit readiness

It does not write to a database.

## AI Execution Example

Run the public-safe synthetic example:

```bash
python examples/ai-execution-synthetic/run_example.py
```

This example proves:

- synthetic request
- synthetic provider adapter
- success and failure normalization
- fallback signal
- confidence and risk extraction
- human escalation
- `AIExecutionResult`

It does not call an external AI API.

## Knowledge Intake Example

Run the public-safe synthetic example:

```bash
python examples/knowledge-intake-synthetic/run_example.py
```

This example proves:

- source identity
- version/status
- knowledge unit to source linkage
- citation/provenance
- retrieval evidence
- issue/conflict
- human-review signal

It does not include private documents, company knowledge, embeddings, vector DBs, prompts, or LLM calls.

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
- `atlas capability show enterprise-intake`
- `atlas capability show ai-execution`
- `atlas capability show knowledge-intake`
- `atlas project inspect <project-path>`
- `atlas file inspect <file>`
- `atlas context`
- `python -m atlas_gateway ...`

## Packaging Note

If you create a real public GitHub repository from this package, initialize a brand-new Git repository from this exported directory only.

Do not push the Git history of an internal training or development repository.
