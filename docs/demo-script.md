# Atlas 60-second Demo

This demo is synthetic, public-safe, and reproducible from a fresh clone. It
does not call an LLM, write a database, or inspect a private project.

[Watch the final 38-second terminal demo](launch/assets/demo.gif).

## Run It

From the Atlas repository root after installation:

```bash
python examples/launch-demo/run_demo.py --target <new-demo-target>
```

The target must not already exist. The script refuses to overwrite files.

## 60-second Talk Track

**0-10 seconds - the task**

```bash
cd examples/enterprise-intake-synthetic
atlas project plan . --task "add Excel import preview with row-level validation"
```

Expected, simplified:

```text
TASK_REUSE
- Tabular Core
- Enterprise Intake
```

Narration: Atlas looks at the current task, not just the repository. This task
needs tabular ingestion plus intake preview semantics, so reuse is worthwhile.

**10-35 seconds - generate the project boundary**

```bash
atlas adapter init enterprise-intake --target <new-demo-target>
```

Reusable from Atlas:

- row decisions
- preview issues
- partial completion
- commit readiness

Still project-owned:

- business validation
- permissions
- database writes and transactions

Narration: Atlas provides the reusable contract and adapter shape. It does not
invent business rules or write production data.

**35-55 seconds - show that Atlas exits**

```bash
cd ../no-atlas-reuse
atlas project plan . --task "update README wording"
```

Expected: `NO_ATLAS_REUSE`.

Narration: Atlas does not force itself into every task. Here the correct result
is to continue normal development.

**55-60 seconds - next step**

Run `atlas project plan . --task "your current task"` in your own project and
review the boundary before adding a dependency or generating an adapter.
