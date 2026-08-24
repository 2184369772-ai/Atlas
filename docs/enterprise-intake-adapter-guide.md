# Atlas Enterprise Intake Adapter Guide

Use Enterprise Intake only through a project-side adapter.

Minimal flow:

1. Read the source file through Tabular Core.
2. Build a project adapter with field mapping, row evaluation, duplicate policy, and trace metadata hooks.
3. Build a preview with `build_preview_with_adapter(...)`.
4. Review row decisions, issues, and commit readiness.
5. Keep persistence on the project side.

Atlas does not own:

- duplicate keys
- business validation rules
- ImportBatch tables
- transactions
- ORM / JDBC
- database writes

Enterprise Intake is `REFERENCE_ONLY`. It must not be treated as a ready-made
import framework.
