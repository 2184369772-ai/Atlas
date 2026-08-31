# Atlas

> Atlas helps AI coding tools decide when proven engineering contracts can be
> reused instead of redesigning the same patterns from scratch.

Atlas is a software engineering reuse framework for developers and AI/Codex.
It scans a project and the current task, then recommends a controlled package,
a reference contract, project-level awareness, or `NO_ATLAS_REUSE`.

Atlas 是给开发者和 AI/Codex 使用的软件工程复用框架。它帮助你判断当前任务
是否值得复用已有工程契约，而不是每次从零重新设计；不合适时会明确退出。

**Why not ask Codex to build everything from scratch?** Codex is still the
developer. Atlas gives it governed contracts and boundaries for recurring
engineering problems, so the project can keep its own business rules while
avoiding unnecessary redesign.

Best fits: structured Excel/CSV intake, normalized execution outcomes,
knowledge provenance, file/config lifecycle, traceability, exports, and
attention routing. Atlas is still `1.1.0-alpha`: use it on bounded tasks and
review every adoption decision.

**Demo:** [Run the reproducible 60-second walkthrough](docs/demo-script.md).

## Try Atlas In 5 Minutes

```bash
git clone https://github.com/2184369772-ai/Atlas.git
pip install git+https://github.com/2184369772-ai/Atlas.git
atlas doctor
cd Atlas/examples/enterprise-intake-synthetic
atlas project plan . --task "add Excel import preview with row decisions"
python run_example.py
```

Expected plan, simplified:

```text
TASK_REUSE
- Tabular Core
- Enterprise Intake
```

The example then prints row decisions, issues, partial completion, and commit
readiness without writing a database. In your own project, run the same plan
command from the project root. Only generate an adapter after reviewing the
boundary:

```bash
atlas adapter init enterprise-intake --target your-project
```

Atlas also knows when to stay out:

```bash
cd ../no-atlas-reuse
atlas project plan . --task "update README wording"
```

Expected: `NO_ATLAS_REUSE`. A project can also return `PROJECT_RELEVANT` when
Atlas may fit the repository but should not be adopted for the current task.

中文快速说明：安装后先运行 `atlas doctor`，再在项目目录执行
`atlas project plan . --task "当前开发任务"`。只有返回 `TASK_REUSE` 时才考虑
直接接入；`TASK_REFERENCE` 只参考契约；`PROJECT_RELEVANT` 或
`NO_ATLAS_REUSE` 时继续正常开发即可。

## Understand The Decision

| Decision | What to do |
| --- | --- |
| `TASK_REUSE` | Reuse the named controlled package/API/adapter and keep project-owned hooks. |
| `TASK_REFERENCE` | Read the contract and boundary; implement inside the project. |
| `PROJECT_RELEVANT` | Atlas may fit another task in this repository; do not adopt it now. |
| `NO_ATLAS_REUSE` | Continue without Atlas. This is a successful routing result. |

Atlas does not call an LLM to make this decision and does not upload or collect
your repository, source code, task text, or project data.

## What Atlas Can Help With

- **Project and task analysis:** inspect a repository, route the current task,
  and show Atlas-owned versus project-owned work.
- **Tabular / Excel / CSV:** workbook, sheet, header, row, cell, value, issue,
  and warning semantics.
- **Enterprise Intake:** preview, row decisions, issues, partial completion,
  duplicate/idempotency boundary, and commit readiness.
- **AI Execution:** request/result, provider failure normalization, fallback,
  evidence, confidence/risk, escalation, trace, and outcome.
- **Knowledge Intake:** source identity, version/status, source linkage,
  citation/provenance, retrieval evidence, conflict, and review signals.
- **Operation Outcome:** status, issue, affected/remaining scope, evidence,
  confidence/risk, fallback, and human attention.
- **File Lifecycle / Runtime Config:** governed lifecycle and effective-config
  semantics while storage, deployment, secrets, and persistence stay local.
- **Traceability / Audit, Report / Export, Attention Routing:** reusable
  engineering semantics without replacing project workflow, RBAC, BI, or delivery.
- **Project Adoption:** `project inspect`, task-aware `project plan`, bounded
  adapter scaffolds, and explicit `NO_ATLAS_REUSE`.

## Capability Maturity

`CONTROLLED_REUSE` means a governed reuse path exists. It does not mean a Stable
Framework Module and it never removes the project-owned adapter/business boundary.

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

Data Model Evolution is not part of the public capability catalog.

## Python And Java Quickstarts

The Python quickstart is the same synthetic Enterprise Intake example used in
the 5-minute path:

```bash
python examples/enterprise-intake-synthetic/run_example.py
```

The Java bridge quickstart generates and compiles project-local scaffold for
the two supported capabilities:

```powershell
powershell -ExecutionPolicy Bypass -File examples/java-bridge-quickstart/run.ps1
```

```bash
bash examples/java-bridge-quickstart/run.sh
```

Java runtime does not depend on Python or Atlas after generation. Java Bridge
v0.1 only supports Enterprise Intake and Operation Outcome; it is not a complete
Java Atlas framework. The generated scaffold contains contract structures and
TODO hooks, never business fields, SQL, DB writes, permissions, prompts, or
business rules.

## Codex Skill

```bash
atlas skill install
atlas skill status
```

Then open a new Codex task and describe your normal development request. The
Skill helps Codex query Atlas Gateway when suitable. It does not guarantee every
session will auto-trigger or hot-load, and it never forces Atlas into every project.

## Common Commands

```bash
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

## When Not To Use Atlas

Do not adopt Atlas merely because a repository contains Excel files, config,
reports, uploads, dashboards, or UI. Local bug fixes, permissions, minor
compatibility fixes, and existing page edits often produce `PROJECT_RELEVANT`
or `NO_ATLAS_REUSE`.

Atlas is not a universal AI coding agent, full-system generator, private-code
learning system, Workflow/Auth/RBAC platform, RAG platform, BI platform, or a
framework every project must use.

## External Beta

Read [External Beta Guide](docs/external-beta.md) before trying Atlas on a real
task. Feedback is welcome through the GitHub Issue templates. Never attach
private source code, secrets, databases, internal paths, company data, or other
sensitive material to a public Issue.

This public alpha contains synthetic examples and public-safe boundaries. It
does not contain private project identities, evidence, credentials, internal
provenance, or real project source code.

## License

Apache-2.0
