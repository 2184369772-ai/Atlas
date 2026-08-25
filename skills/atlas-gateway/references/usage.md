# Atlas Gateway Skill Usage

## Trigger Guidance

Use this skill when all of the following are true:

- the work is in a software project
- Atlas may or may not help
- you need a conservative reuse decision before inventing new layers

Do not use it just for ordinary coding when Atlas is irrelevant.

## Scenario A: Atlas Has Value

Expected chain:

```text
new project
-> project inspect
-> project plan
-> CONTROLLED_REUSE
-> capability show tabular-core
-> file inspect
-> keep adapter and business rules in the project
```

For Candidate adapter boundaries, only run `adapter init` after the task explicitly asks to connect Atlas.

## Scenario B: Atlas Has No Value

Expected chain:

```text
new project
-> project inspect
-> NO_ATLAS_REUSE
-> continue normal project development
```

Do not force Atlas into the project after a `NO_ATLAS_REUSE` result.

## Scenario C: Adapter Scaffold

Supported scaffolds:

- `enterprise-intake`
- `ai-execution`
- `knowledge-intake`

The scaffold is project-owned. It must not generate business fields, prompts, SQL, database writes, permissions, RAG strategy, or real business rules.

## Maturity Discipline

- `REFERENCE_ONLY` stays Candidate-only.
- `SEMANTIC_REFERENCE` stays semantic-only.
- `INBOX_ONLY` stays Inbox-only.
- The skill must never upgrade maturity on its own.

## Gateway Missing

If the runner cannot locate Atlas Gateway:

- say that Gateway could not be found
- explain the non-destructive next step
- do not fabricate Atlas capability advice from memory
