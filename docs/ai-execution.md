# AI Execution

AI Execution is an Atlas Candidate for normalizing the result boundary around AI-backed execution.

Governance: `ATLAS CANDIDATE / SHADOW_VALIDATED`

Recommendation: `REFERENCE_ONLY`

It is validated through isolated read-only shadow comparison across multiple real project implementations. This public package does not include private project material and does not imply real production model calls.

## Atlas Scope

Atlas AI Execution covers:

- execution request/result
- failure normalization
- fallback signal
- evidence reference
- confidence/risk
- human escalation
- trace/outcome

## Project Adapter Scope

Your project owns:

- provider calls
- provider request/response formats
- retry/timeout implementation
- prompts
- model choice
- RAG/Knowledge
- business rules
- persistence

## Non-Goals

AI Execution is not:

- an AI Agent platform
- a prompt framework
- a RAG framework
- a model SDK replacement
- a workflow system

## Public Example

Run:

```bash
python examples/ai-execution-synthetic/run_example.py
```

The example uses a synthetic provider adapter only. It does not call an external AI API.
