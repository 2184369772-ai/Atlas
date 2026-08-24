# Knowledge Intake Boundary

Knowledge Intake gives projects a small public-safe contract for preserving knowledge source identity, source-to-unit linkage, citations, retrieval evidence, conflicts, and review signals.

## Recommendation

`REFERENCE_ONLY`

This means the package may be inspected and used as a reference implementation, but it is not a stable platform promise.

## Safe Reuse

Use the public package to model:

- `KnowledgeSource`
- `KnowledgeUnit`
- `KnowledgeCitation`
- `RetrievalEvidence`
- `KnowledgeIssue`
- `KnowledgeIntakeSnapshot`
- source version/status semantics
- citation/provenance preservation
- issue/conflict and human-review signaling

## Adapter Responsibility

The host project remains responsible for:

- OCR and parsing
- chunking
- embeddings and vector databases
- retrieval and ranking strategy
- prompts and LLM calls
- business knowledge
- persistence and permissions

Do not treat Atlas Knowledge Intake as a RAG platform, knowledge base platform, or search engine.
