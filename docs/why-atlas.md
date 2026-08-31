# Why Atlas

Consider a synthetic feature: add an Excel import preview with row-level
validation before any database write.

## Without Atlas

The coding agent and developer must design the same engineering semantics again:

- What are the row decisions: accept, skip, reject, or review?
- How are structural and business issues represented?
- What does partial completion mean?
- When is the preview ready to commit, blocked, or waiting for review?
- Which behavior belongs in a reusable contract and which belongs in the project?

That design may work, but every new implementation can choose different names,
states, issue shapes, and boundaries.

## With Atlas

The task-aware plan identifies Tabular Core and Enterprise Intake. The project
can reuse the existing package, contract, and adapter semantics for row
decisions, preview issues, partial completion, and commit readiness.

The project still implements its own fields, mapping, business validation,
duplicate policy, permissions, persistence, transactions, and database writes.
Atlas reduces repeated engineering design; it does not replace project logic.
