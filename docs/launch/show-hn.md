# Show HN Draft

## Title

Show HN: Atlas - Task-aware reusable engineering contracts for coding agents

## Text

Coding agents often redesign recurring engineering semantics from scratch. I
built Atlas to let a coding agent ask whether the current task should reuse an
existing contract before it starts implementing.

```bash
atlas project plan . --task "add Excel import preview with row-level validation"
```

The result is one of `TASK_REUSE`, `TASK_REFERENCE`, `PROJECT_RELEVANT`, or
`NO_ATLAS_REUSE`. A controlled reuse result identifies the relevant package or
contract and keeps business rules, permissions, persistence, and production
writes inside the project. An unrelated task makes Atlas exit instead of adding
another abstraction.

The repository includes a reproducible synthetic 60-second demo, Python
quickstart, a limited Java scaffold bridge, and a Codex Skill:
https://github.com/2184369772-ai/Atlas

Atlas is `1.1.0-alpha` and in External Beta, not a stable framework release. I
am looking for feedback on task-routing accuracy and whether the reuse boundary
is clear enough to be useful in real development.
