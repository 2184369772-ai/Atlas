# Atlas Gateway

Atlas Gateway is the runtime entry point for Atlas public usage.

Use it to:

- list current capabilities
- inspect a software project conservatively
- plan Atlas adoption without guessing business rules
- create minimal project-owned adapter scaffolds for supported Candidate boundaries
- diagnose the local Gateway environment
- inspect CSV/XLSX files through Atlas Consumer Bridge
- query the current Enterprise Intake Candidate without upgrading its maturity
- query the current AI Execution Candidate without upgrading its maturity
- query the current Knowledge Intake Candidate without upgrading its maturity
- generate a short public-safe context pack

Commands:

```bash
atlas capability list
atlas capability show tabular-core
atlas capability show enterprise-intake
atlas capability show ai-execution
atlas capability show knowledge-intake
atlas project inspect <project-path>
atlas project plan <project-path>
atlas adapter init enterprise-intake --target <project-path>
atlas adapter init ai-execution --target <project-path>
atlas adapter init knowledge-intake --target <project-path>
atlas doctor
atlas file inspect <file>
atlas context
```

Compatibility command:

```bash
python -m atlas_gateway capability list
```

Gateway facts are the runtime source of truth. Do not guess current maturity from stale notes.

`adapter init` refuses semantic-only and inbox-only capabilities, and does not overwrite existing files unless `--force` is explicit.
