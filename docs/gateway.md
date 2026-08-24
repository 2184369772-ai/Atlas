# Atlas Gateway

Atlas Gateway is the runtime entry point for Atlas public usage.

Use it to:

- list current capabilities
- inspect a software project conservatively
- inspect CSV/XLSX files through Atlas Consumer Bridge
- query the current Enterprise Intake Candidate without upgrading its maturity
- query the current AI Execution Candidate without upgrading its maturity
- generate a short public-safe context pack

Commands:

```bash
atlas capability list
atlas capability show tabular-core
atlas capability show enterprise-intake
atlas capability show ai-execution
atlas project inspect <project-path>
atlas file inspect <file>
atlas context
```

Compatibility command:

```bash
python -m atlas_gateway capability list
```

Gateway facts are the runtime source of truth. Do not guess current maturity from stale notes.
