# Getting Started

## Install

```bash
python -m venv .venv
pip install -e .
```

## Verify

```bash
atlas capability list
atlas capability show enterprise-intake
atlas capability show ai-execution
atlas project inspect .
```

## Tabular Example

```bash
atlas file inspect path/to/file.csv
atlas file inspect path/to/file.xlsx
```

## Context Pack

```bash
atlas context --output ATLAS_CONTEXT.md
```

The generated context pack is designed to be public-safe and shareable with Codex, ChatGPT, or other AI tools.

## Enterprise Intake Example

```bash
python examples/enterprise-intake-synthetic/run_example.py
```

## AI Execution Example

```bash
python examples/ai-execution-synthetic/run_example.py
```

This example uses only a synthetic provider adapter.
