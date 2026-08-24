# Getting Started

## Install

```bash
python -m venv .venv
pip install -e .
```

## Verify

```bash
atlas capability list
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
