# Atlas

Atlas is a software engineering reuse framework for developers and AI/Codex. It scans the current project, decides whether existing Atlas capabilities are worth reusing, and when appropriate provides validated Core, Adapter, and engineering semantics from real project work. When Atlas is not a fit, it clearly returns `NO_ATLAS_REUSE`.

Current public package version: `1.0.0-alpha`

License: `Apache-2.0`

## Quick Start

```bash
pip install git+https://github.com/2184369772-ai/Atlas.git

atlas doctor
atlas capability list

cd your-project
atlas project inspect .
atlas project plan .
```

Codex users can also install the Atlas Skill:

```bash
atlas skill install
atlas skill status
```

Then open a new Codex task and describe your normal development request.

## What Atlas Can Help With

### Project Analysis

- Scan a new software project.
- Decide whether Atlas has useful reuse value.
- Produce an adoption plan.
- Make clear what must stay project-owned.

### Tabular / Excel / CSV

- Read CSV/XLSX files into structured JSON.
- Preserve sheet, header, row, and cell semantics.
- Report issues and warnings.
- Help with pre-processing before complex spreadsheet import flows.

### Enterprise Intake

- Preview and dry-run semantics.
- Row-level `ACCEPT`, `SKIP`, `REJECT`, and `REVIEW`.
- Partial completion.
- Duplicate and idempotency semantics.
- Commit readiness.
- Clear Adapter boundary.

### AI Execution

- Standardized AI execution request/result shape.
- Provider failure, timeout, and invalid-result normalization.
- Fallback signal.
- Evidence reference.
- Confidence and risk.
- Human escalation.

### Knowledge Intake

- Knowledge source identity.
- Source version and status.
- Knowledge unit to source linkage.
- Citation and provenance.
- Conflict and review signal.
- Retrieval evidence.

### File Lifecycle

- File/source identity.
- File metadata and checksum when available.
- Reference and availability semantics.
- Lifecycle state and state transition checks.
- Retention intent.
- File-level issues.

### Operation Outcome

- Shared operation-result status.
- Issues and warnings.
- Evidence references.
- Affected and remaining scope.
- Confidence and risk.
- Fallback and human-attention signal.

### Project Adoption

- `atlas project inspect`
- `atlas project plan`
- `atlas adapter init`
- Adapter scaffold for supported Candidate boundaries.
- `NO_ATLAS_REUSE` when Atlas is not useful.

### Codex Skill

After installing the Skill, Codex can use Atlas Gateway during suitable software engineering tasks to decide whether Atlas should be reused.

Current honest limits:

- Not every Codex session is guaranteed to trigger the Skill automatically.
- Hot reload is not guaranteed; a new Codex task is usually more reliable after installation.
- Atlas does not force every project to use Atlas.
- `NO_ATLAS_REUSE` is a correct and expected result for many projects.

## Practical Examples

```text
Project contains a complex Excel import
        |
atlas project inspect .
        |
Finds Tabular / Enterprise Intake signals
        |
atlas project plan .
        |
atlas adapter init enterprise-intake --target .
        |
Project fills in its own fields, validation, and database logic
```

```text
Ordinary small project
        |
atlas project inspect .
        |
NO_ATLAS_REUSE
        |
Continue normal development without adding Atlas
```

## Capability Maturity

| Capability | Public maturity / recommendation |
| --- | --- |
| Tabular Core | `CONTROLLED_REUSE` |
| Enterprise Intake | `SHADOW_VALIDATED / REFERENCE_ONLY` |
| AI Execution | `SHADOW_VALIDATED / REFERENCE_ONLY` |
| Knowledge Intake | `SHADOW_VALIDATED / REFERENCE_ONLY` |
| File Lifecycle | `SHADOW_VALIDATED / REFERENCE_ONLY` |
| Operation Outcome | `SHADOW_VALIDATED / REFERENCE_ONLY` |
| Runtime Config | `SHADOW_VALIDATED / REFERENCE_ONLY` |

Candidate capabilities are not Stable Modules. They are useful references with explicit boundaries, and real projects must still provide their own adapters and business logic.

## Common Commands

```bash
atlas setup
atlas doctor
atlas capability list
atlas capability show enterprise-intake
atlas project inspect .
atlas project plan .
atlas adapter init enterprise-intake --target .
atlas adapter init ai-execution --target .
atlas adapter init knowledge-intake --target .
atlas file inspect path/to/file.csv
atlas context
atlas skill install
atlas skill status
atlas skill uninstall
```

## Atlas Is Not

Atlas is not:

- a universal AI coding agent
- a platform that automatically generates complete systems
- a system that automatically learns private code
- a Workflow/Auth/RBAC platform
- a RAG platform
- a framework that must be used in every project

## Public Safety

This public alpha contains only public-safe code, synthetic examples, and public-safe tests. Shadow-validated Candidates may say they were validated through isolated read-only shadow comparison across multiple real project implementations, but this repository does not include private project names, company evidence, private paths, prompts, credentials, or internal provenance.

## Packaging Note

This repository is the public distribution. It does not carry private development history.
