# Atlas

Atlas is a software engineering reuse framework for developers and AI/Codex.
It scans a project, checks whether existing Atlas capabilities are worth using,
and gives a task-aware adoption plan. When Atlas is not useful, it says
`NO_ATLAS_REUSE` instead of forcing a dependency.

Atlas 是给开发者和 AI/Codex 使用的软件工程复用框架。它不只判断“这个项目
有没有 Atlas 相关能力”，还会判断“当前任务值不值得接 Atlas”。

Current public package version: `1.1.0-alpha`

License: `Apache-2.0`

## Quick Start

```bash
pip install git+https://github.com/2184369772-ai/Atlas.git

atlas doctor
atlas capability list

cd your-project
atlas project inspect .
atlas project plan . --task "current development task"
```

Codex users can install the Atlas Skill:

```bash
atlas skill install
atlas skill status
```

Then open a new Codex task and describe your normal development request.
The Skill helps Codex query Atlas Gateway when the task is suitable. It does
not guarantee every session will auto-trigger, and Atlas never forces every
project to use Atlas.

## What Atlas Can Help With

### Project And Task Analysis

- Scan a software project for Atlas-relevant signals.
- Distinguish project-level relevance from current-task reuse.
- Produce an adoption plan with capability maturity, project-owned work, adapter hooks, and boundaries.
- Return `NO_ATLAS_REUSE` when Atlas does not help.

Task-aware routing:

```bash
atlas project plan . --task "add Excel import preview with row decisions"
```

Task decisions:

- `TASK_REUSE`: the current task should use a controlled Atlas package, API, adapter, or bridge.
- `TASK_REFERENCE`: Atlas semantics are useful as reference, but implementation stays project-owned.
- `PROJECT_RELEVANT`: the project has Atlas-relevant patterns, but the current task should not adopt Atlas.
- `NO_ATLAS_REUSE`: no useful Atlas reuse for this project or task.

### Tabular / Excel / CSV

- CSV/XLSX structured reading.
- Workbook, sheet, header, row, and cell semantics.
- Structural issues and warnings.
- Pre-processing before complex spreadsheet import flows.

### Enterprise Intake

- Preview and dry-run semantics.
- Row-level `ACCEPT`, `SKIP`, `REJECT`, and `REVIEW`.
- Partial completion and commit readiness.
- Adapter boundary for business validation, duplicate policy, persistence, transaction, and DB writes.

### AI Execution

- Execution request/result semantics.
- Provider failure, timeout, invalid-result normalization.
- Fallback signal, evidence reference, confidence/risk, and human escalation.
- Project-owned prompt, model choice, provider calls, retry/timeout, RAG, business rules, and persistence.

### Knowledge Intake

- Knowledge source identity, version, and status.
- Knowledge unit to source linkage.
- Citation/provenance, retrieval evidence, conflicts, and human-review signal.
- Project-owned parser/OCR, chunking, embeddings/vector DB, retrieval/ranking, prompt/LLM, permissions, and persistence.

### Operation Outcome

- Shared operation-result status.
- Issues, affected scope, remaining scope, evidence, confidence/risk, fallback, and human attention.
- Not an API envelope, workflow engine, approval platform, exception framework, notification system, audit log, or business state machine.

### File Lifecycle

- File/source identity, metadata, reference, lifecycle state, retention intent, issues, and transition checks.
- Project-owned upload/download, storage, permissions, approvals, business version rules, and database transactions.

### Runtime Config

- Config key/spec, effective values, issue expression, provenance, safe public serialization, and config comparison.
- Project-owned framework integration, deployment, config center, business defaults, and secret management.

### Traceability / Audit

- Source identity, actor/producer, timestamp, event/change, before/after, reason, evidence/reference, correlation/task id, and trace-chain integrity.
- Not a logging platform, audit-log database, RBAC system, compliance retention engine, or business audit content library.

### Report / Export Semantics

- Source facts, dimensions, metric roles, planned/actual/variance semantics, report snapshots, export projections, issues, and source trace.
- Project-owned formulas, SQL/ORM, BI, permissions, page design, Excel styling, and export fields.

### Notification / Attention Routing

- Event-triggered attention semantics: audience, level, reason, source reference, due/reminder metadata, acknowledgement, resolution, dismissal, escalation, and dedupe metadata.
- Project-owned delivery, users/org structure, workflow, permissions, scheduling, storage, and business escalation rules.

### Java Cross-language Bridge v0.1

Atlas can generate Java scaffold from Atlas contracts for selected capabilities:

```bash
atlas adapter init enterprise-intake --target your-java-project --language java
atlas adapter init operation-outcome --target your-java-project --language java
```

Boundary:

- Java runtime does not depend on Python or the Atlas CLI after scaffold generation.
- Current Java bridge only supports Enterprise Intake and Operation Outcome.
- It is not a complete Java Atlas framework.
- Generated scaffold contains contract/semantic structures and TODO hooks, not business fields, SQL, DB writes, permissions, prompts, or business rules.

### Codex Skill

After installing the Skill, Codex can use Gateway for suitable software
engineering tasks:

```text
project inspect
-> project plan --task "current task"
-> adapter init only when the task explicitly needs Atlas adoption
-> normal project development
```

The Skill accepts `NO_ATLAS_REUSE`. It should not write scaffold into a project
unless the user task explicitly asks to connect Atlas.

## Capability Maturity

`CONTROLLED_REUSE` means a governed reuse path exists. It does not mean a Stable
Framework Module, and it does not remove the project-owned adapter/business
boundary.

| Capability | Public maturity / recommendation |
| --- | --- |
| Tabular Core | `CONTROLLED_REUSE` |
| Enterprise Intake | `SHADOW_VALIDATED / CONTROLLED_REUSE` |
| AI Execution | `SHADOW_VALIDATED / CONTROLLED_REUSE` |
| Knowledge Intake | `SHADOW_VALIDATED / CONTROLLED_REUSE` |
| Operation Outcome | `SHADOW_VALIDATED / CONTROLLED_REUSE` |
| File Lifecycle | `SHADOW_VALIDATED / CONTROLLED_REUSE` |
| Runtime Config | `SHADOW_VALIDATED / CONTROLLED_REUSE` |
| Traceability / Audit | `SHADOW_VALIDATED / CONTROLLED_REUSE` |
| Report / Export Semantics | `SHADOW_VALIDATED / CONTROLLED_REUSE` |
| Notification / Attention Routing | `SHADOW_VALIDATED / CONTROLLED_REUSE` |
| Business Rule Modeling | `SHADOW_VALIDATED / REFERENCE_ONLY` |
| Dashboard / Decision Workspace | `SHADOW_VALIDATED / REFERENCE_ONLY` |
| UI Quality & Interaction Reliability | `SHADOW_VALIDATED / REFERENCE_ONLY` |

Data Model Evolution remains outside the public capability catalog.

## When Not To Use Atlas

Do not adopt Atlas just because a repository contains Excel files, config files,
reports, uploads, dashboards, or UI code. Local bug fixes, permission closeout,
minor compatibility fixes, and existing approval-page edits often produce
`PROJECT_RELEVANT` or `NO_ATLAS_REUSE`.

## Common Commands

```bash
atlas setup
atlas doctor
atlas capability list
atlas capability show enterprise-intake
atlas project inspect .
atlas project plan . --task "current development task"
atlas adapter init enterprise-intake --target .
atlas adapter init operation-outcome --target . --language java
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
- a system that learns private code
- a Workflow/Auth/RBAC platform
- a RAG platform
- a BI/dashboard platform
- a complete Java framework
- a framework that must be used in every project

## Public Safety

This public alpha contains public-safe code, synthetic examples, public-safe
tests, and capability boundaries. It may state that capabilities were validated
through isolated read-only comparison across multiple real project
implementations, but this repository does not include private project names,
company evidence, private paths, prompts, credentials, internal provenance, or
real project source code.

## Packaging Note

This repository is the public distribution. It does not carry private
development history.
