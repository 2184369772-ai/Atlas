# Reddit Draft

## Title

I got tired of coding agents redesigning the same engineering patterns from scratch, so I built Atlas

## Post

Coding agents are good at producing code, but I kept seeing the same engineering
semantics redesigned from scratch: import preview states, row-level decisions,
normalized operation outcomes, provenance, lifecycle, and similar boundaries.

I built Atlas as a task-aware reuse layer for developers and coding agents. You
run a plan against the current project and task:

```bash
atlas project plan . --task "add Excel import preview with row-level validation"
```

Atlas returns one of four decisions: `TASK_REUSE`, `TASK_REFERENCE`,
`PROJECT_RELEVANT`, or `NO_ATLAS_REUSE`. For the synthetic Excel intake demo it
recommends Tabular Core and Enterprise Intake, then Atlas can generate a small
project-side adapter boundary. Business validation, permissions, persistence,
and database writes remain in the project.

It also deliberately exits for unrelated work. A README-only task in the demo
returns `NO_ATLAS_REUSE`.

Reproducible 60-second demo:
https://github.com/2184369772-ai/Atlas/blob/main/docs/demo-script.md

Repository:
https://github.com/2184369772-ai/Atlas

Atlas is currently `1.1.0-alpha` and in External Beta. `CONTROLLED_REUSE` does
not mean a stable framework module, and task routing can still be wrong. I would
especially value discussion about false reuse recommendations, missed reuse
opportunities, and whether the project/adapter boundary is understandable.

Please use synthetic or redacted examples in public feedback; do not post
private source code, secrets, databases, internal paths, or company data.
