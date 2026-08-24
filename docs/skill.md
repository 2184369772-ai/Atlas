# Atlas Skill

The Atlas Codex skill helps Codex decide whether Atlas should be checked for a software project, then routes through Atlas Gateway instead of reimplementing Atlas behavior.

Install the skill locally:

```bash
python skills/atlas-gateway/scripts/install_local.py install
```

Check the install:

```bash
python skills/atlas-gateway/scripts/install_local.py status
python skills/atlas-gateway/scripts/run_gateway.py --status
```

Real limitations:

- install the skill first
- a new task or session is more reliable than expecting hot reload
- Atlas is not guaranteed to trigger for every task
- the skill still accepts `NO_ATLAS_REUSE`
- the skill uses Gateway as the runtime fact source
