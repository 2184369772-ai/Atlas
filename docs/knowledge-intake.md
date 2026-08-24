# Knowledge Intake

Knowledge Intake is an Atlas Candidate for source-backed knowledge intake and retrieval evidence semantics.

Governance: `ATLAS CANDIDATE / SHADOW_VALIDATED`

Recommendation: `REFERENCE_ONLY`

It is validated through isolated read-only shadow comparison across multiple real project implementations. This public package does not include private project material, company knowledge, source documents, question sets, or internal evidence.

## Atlas Scope

Atlas Knowledge Intake covers:

- source identity
- version/status
- knowledge unit to source linkage
- citation/provenance
- retrieval evidence
- issue/conflict
- human-review signal

## Project Scope

Your project owns:

- OCR/parser
- chunking
- embedding/vector DB
- retrieval/ranking strategy
- prompts and LLMs
- business knowledge
- persistence
- permissions

## Non-Goals

Knowledge Intake is not:

- a RAG platform
- a knowledge base platform
- a search engine

## Public Example

Run:

```bash
python examples/knowledge-intake-synthetic/run_example.py
```

The example uses only synthetic sources, units, citations, retrieval evidence, and review signals.
