# Atlas External Beta Guide

Atlas `1.1.0-alpha` is ready for bounded external evaluation. It is not a stable
framework release.

## Who Should Try It

Atlas is a good beta fit for developers using Codex or another AI coding tool
on an existing software project, especially when the task involves structured
imports, normalized outcomes, provenance, lifecycle, traceability, exports, or
attention routing.

Start with one small, real task that has a clear before/after result. Avoid a
production-wide migration, a security-critical rewrite, or a task that requires
Atlas to invent business rules.

## Run Task-aware Planning

From your project root:

```bash
atlas doctor
atlas project plan . --task "one-sentence description of the current task"
```

- `TASK_REUSE`: review the named capability boundary, then use its package,
  API, or generated adapter while keeping business rules and persistence local.
- `TASK_REFERENCE`: use the contract as design guidance; do not assume a
  drop-in implementation.
- `PROJECT_RELEVANT`: Atlas may fit the project, but not this task. Continue
  without adopting it now.
- `NO_ATLAS_REUSE`: continue normally without Atlas.

Do not force a reuse result. A correct `NO_ATLAS_REUSE` is useful.

## Give Safe Feedback

Use the repository's GitHub Issue templates for beta feedback, routing problems,
or installation/runtime problems. Share the smallest synthetic reproduction you
can.

Do not upload company source code, proprietary data, secrets, tokens, database
files or connection strings, internal paths, private evidence, or sensitive
screenshots. Redact project identity and business data before posting.
