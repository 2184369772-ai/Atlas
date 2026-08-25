# Atlas Skill

The Atlas Codex skill helps Codex decide whether Atlas should be checked for a software project, then routes through Atlas Gateway instead of reimplementing Atlas behavior.

Install the skill locally:

```bash
atlas skill install
```

Check the install:

```bash
atlas skill status
atlas doctor
```

Real limitations:

- install the skill first
- new projects should use `project inspect` before `project plan`
- adapter scaffolds are generated only when the task explicitly asks to connect Atlas
- a new task or session is more reliable than expecting hot reload
- Atlas is not guaranteed to trigger for every task
- the skill still accepts `NO_ATLAS_REUSE`
- the skill uses Gateway as the runtime fact source
