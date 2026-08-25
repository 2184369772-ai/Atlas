# Capability Boundaries

## Tabular Core

- Recommendation: `CONTROLLED_REUSE`
- Use when a project needs read-only CSV/XLSX structure and value semantics.
- Keep business sheet selection, field mapping, validation, workflow, and database writes in the project.

## Enterprise Intake

- Recommendation: `REFERENCE_ONLY`
- Governance: `ATLAS CANDIDATE / SHADOW_VALIDATED`
- Use when a project needs tabular preview, row decision, issue aggregation, partial completion, and commit readiness between Tabular Core and project-side writes.
- Keep duplicate policy, business validation, persistence, transaction handling, and DB writes in the project adapter.
- This is not a Stable Module and not a universal import framework.

## AI Execution

- Recommendation: `REFERENCE_ONLY`
- Governance: `ATLAS CANDIDATE / SHADOW_VALIDATED`
- Atlas owns execution request/result semantics, failure normalization, fallback signal, evidence reference, confidence/risk, human escalation, trace, and outcome.
- The project adapter owns provider calls, provider request/response formats, retry/timeout implementation, prompts, model choice, RAG/Knowledge, business rules, and persistence.
- This is not a Stable Module, AI Agent platform, prompt framework, RAG framework, model SDK replacement, or workflow system.
- Public validation statement: validated through isolated read-only shadow comparison across multiple real project implementations.
- Public validation does not imply real production model calls.

## Knowledge Intake

- Recommendation: `REFERENCE_ONLY`
- Governance: `ATLAS CANDIDATE / SHADOW_VALIDATED`
- Atlas owns source identity, version/status, knowledge unit to source linkage, citation/provenance, retrieval evidence, issue/conflict, and human-review signal.
- The project adapter owns OCR/parser, chunking, embedding/vector DB, retrieval/ranking strategy, prompts/LLMs, business knowledge, persistence, and permissions.
- This is not a Stable Module, RAG platform, knowledge base platform, or search engine.
- Public validation statement: validated through isolated read-only shadow comparison across multiple real project implementations.

## Runtime Config

- Recommendation: `REFERENCE_ONLY`
- Governance: `ATLAS CANDIDATE / SHADOW_VALIDATED`
- Use as a reference implementation for config key/spec, source, required/default handling, type conversion, issue expression, effective value provenance, safe public serialization, and Shadow comparison.
- Keep framework-specific configuration structures, config centers, deployment scripts, business defaults, and secret management in the project adapter.

## File Lifecycle

- Recommendation: `REFERENCE_ONLY`
- Governance: `ATLAS CANDIDATE / SHADOW_VALIDATED`
- Use as a boundary or adapter reference, not as a forced dependency.

## Operation Outcome

- Recommendation: `REFERENCE_ONLY`
- Governance: `ATLAS CANDIDATE / SHADOW_VALIDATED`
- Use as a reference implementation for shared operation-result semantics.
- Keep API shape, workflow, approval, notification, audit log, and business state machine concerns in the project.

## General Rule

`NO_ATLAS_REUSE` is a normal outcome. Atlas should not be forced into a project that does not benefit from it.
