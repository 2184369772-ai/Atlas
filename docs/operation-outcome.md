# Operation Outcome

Atlas Operation Outcome is a reference-level Candidate for shared operation-result semantics.

It covers:

- status
- issues and warnings
- evidence references
- affected and remaining scope
- confidence and risk
- fallback signal
- human-attention signal
- trace metadata

It is not an API response envelope, workflow engine, approval system, exception framework, notification service, audit log, or business state machine.

Minimal example:

```bash
python examples/operation-outcome-synthetic/run_example.py
```
