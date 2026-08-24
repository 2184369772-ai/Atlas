# AI Execution Boundary

AI Execution gives projects a small result contract for AI-backed operations while keeping provider-specific and business-specific behavior outside Atlas.

## Recommendation

`REFERENCE_ONLY`

This means the package may be inspected and used as a reference implementation, but it is not a stable platform promise.

## Safe Reuse

Use the public package to model:

- `AIExecutionRequest`
- provider adapter invocation boundary
- `AIExecutionResult`
- normalized provider failures
- fallback-used signal
- confidence and risk fields
- evidence references
- human escalation flag
- trace and outcome fields

## Adapter Responsibility

The adapter and host project remain responsible for:

- calling the selected provider
- translating provider request/response formats
- retry and timeout behavior
- prompt content
- model selection
- retrieval or knowledge context
- business validation
- storing results

Do not treat Atlas AI Execution as an AI Agent platform, prompt framework, RAG framework, model SDK replacement, or workflow engine.
