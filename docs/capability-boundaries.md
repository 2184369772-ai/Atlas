# Capability Boundaries

## Tabular Core

- Recommendation: `CONTROLLED_REUSE`
- Use when a project needs read-only CSV/XLSX structure and value semantics.
- Keep business sheet selection, field mapping, validation, workflow, and database writes in the project.

## Runtime Config

- Recommendation: `REFERENCE_ONLY`
- Candidate only.
- Use as a design reference, not as a stable package promise.

## File Lifecycle

- Recommendation: `REFERENCE_ONLY`
- Candidate only.
- Use as a boundary or adapter reference, not as a forced dependency.

## Operation Outcome

- Recommendation: `SEMANTIC_REFERENCE`
- Semantic reference only.
- No standalone package is shipped or implied here.

## General Rule

`NO_ATLAS_REUSE` is a normal outcome. Atlas should not be forced into a project that does not benefit from it.
