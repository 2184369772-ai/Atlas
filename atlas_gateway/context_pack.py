from __future__ import annotations

from pathlib import Path

from .catalog import list_capabilities, load_catalog


def build_context_markdown() -> str:
    catalog = load_catalog()
    capabilities = list_capabilities()
    lines = [
        "# ATLAS_CONTEXT",
        "",
        "## What Atlas Is",
        "",
        "Atlas is a small, governance-first capability repository for reusable software patterns.",
        "Atlas Gateway v0.1 gives AI tools and new projects a safe entry point to inspect Atlas capabilities without reading the whole repository.",
        "",
        "## Current Position",
        "",
        f"- Version: {catalog.get('catalog_version', 'atlas-gateway-v0.1')}",
        "- Scope: local CLI only",
        "- Public-safe default: yes",
        "- Core rule: Atlas recommendations must stay conservative and may explicitly return `NO_ATLAS_REUSE`.",
        "",
        "## Current Capabilities",
        "",
    ]

    for capability in capabilities:
        lines.extend(
            [
                f"### {capability['name']}",
                f"- ID: `{capability['id']}`",
                f"- Governance status: {capability['governance_status']}",
                f"- Recommendation: `{capability['recommendation']}`",
                f"- Use via: {capability['use_via']}",
                f"- Can use now: {capability['can_use_now']}",
                f"- Reference only: {capability['reference_only']}",
                f"- Forbidden as ready-made call: {capability['forbidden_as_ready_made_call']}",
                f"- Notes: {capability['notes']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Gateway Commands",
            "",
            "- List capabilities: `python -m atlas_gateway capability list`",
            "- Show one capability: `python -m atlas_gateway capability show tabular-core`",
            "- Inspect a project: `python -m atlas_gateway project inspect <project-path>`",
            "- Inspect a file through Consumer Bridge: `python -m atlas_gateway file inspect <file>`",
            "- Generate this context pack: `python -m atlas_gateway context --output ATLAS_CONTEXT.md`",
            "",
            "## Reuse Rules",
            "",
            "- `CONTROLLED_REUSE` means Atlas has a narrow, governed capability that may be reused carefully.",
            "- `REFERENCE_ONLY` means Atlas has a Candidate that can guide adapters or design, not act as a stable package promise.",
            "- `SEMANTIC_REFERENCE` means Atlas only has a semantic reference and no standalone package.",
            "- `INBOX_ONLY` means the idea stays in the Candidate Inbox and must not be called as an existing Atlas capability.",
            "- `NO_ATLAS_REUSE` is a valid outcome and should be preferred over overclaiming Atlas value.",
            "",
            "## Safety Rule",
            "",
            "This context pack is intentionally public-safe. It excludes private project details, company evidence, local machine paths, ignored review artifacts, and internal provenance details.",
            "",
        ]
    )
    return "\n".join(lines)


def write_context(path: str | Path) -> Path:
    output_path = Path(path)
    output_path.write_text(build_context_markdown(), encoding="utf-8")
    return output_path
