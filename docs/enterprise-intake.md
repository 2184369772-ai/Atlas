# Atlas Enterprise Intake

Atlas Enterprise Intake is the narrow layer between Atlas Tabular Core and
project-side persistence.

Current maturity:

- governance: `ATLAS CANDIDATE / SHADOW_VALIDATED`
- recommendation: `REFERENCE_ONLY`

It is validated through read-only shadow comparison across multiple real
projects, but it is still not a Stable Module and not a universal import
framework.

Atlas owns:

- preview / dry-run semantics
- row decision vocabulary: `ACCEPT`, `SKIP`, `REJECT`, `REVIEW`
- issue aggregation across structure, mapping, row, and field scopes
- partial completion summary
- commit readiness
- caller-visible trace-ready row metadata shape

The project still owns:

- project adapter
- duplicate policy
- business validation
- persistence
- transaction boundary
- database writes
- business sheet and field policy

Enterprise Intake does not read CSV/XLSX directly. It consumes Tabular Core
output.
