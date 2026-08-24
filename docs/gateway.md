# Atlas Gateway

Atlas Gateway is the runtime entry point for Atlas public usage.

Use it to:

- list current capabilities
- inspect a software project conservatively
- inspect CSV/XLSX files through Atlas Consumer Bridge
- generate a short public-safe context pack

Commands:

```bash
atlas capability list
atlas capability show tabular-core
atlas project inspect <project-path>
atlas file inspect <file>
atlas context
```

Compatibility command:

```bash
python -m atlas_gateway capability list
```

Gateway facts are the runtime source of truth. Do not guess current maturity from stale notes.
