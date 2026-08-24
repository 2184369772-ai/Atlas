from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from atlas_consumer.bridge import inspect_file, result_to_payload

from .catalog import get_capability, list_capabilities
from .context_pack import build_context_markdown, write_context
from .inspector import inspect_project, to_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m atlas_gateway",
        description="Atlas Gateway v0.1: inspect Atlas capabilities, projects, files, and public-safe context.",
    )
    subparsers = parser.add_subparsers(dest="group", required=True)

    capability_parser = subparsers.add_parser("capability", help="Query Atlas capability catalog.")
    capability_subparsers = capability_parser.add_subparsers(dest="command", required=True)

    capability_list = capability_subparsers.add_parser("list", help="List Atlas capabilities.")
    capability_list.add_argument("--json", action="store_true", help="Return machine-readable JSON.")

    capability_show = capability_subparsers.add_parser("show", help="Show one Atlas capability.")
    capability_show.add_argument("capability", help="Capability id or name.")
    capability_show.add_argument("--json", action="store_true", help="Return machine-readable JSON.")

    project_parser = subparsers.add_parser("project", help="Inspect a software project for conservative Atlas reuse signals.")
    project_subparsers = project_parser.add_subparsers(dest="command", required=True)
    project_inspect = project_subparsers.add_parser("inspect", help="Inspect one project path.")
    project_inspect.add_argument("project_path", help="Path to the project directory or file.")
    project_inspect.add_argument("--json", action="store_true", help="Return machine-readable JSON.")

    file_parser = subparsers.add_parser("file", help="Inspect one file through Atlas Consumer Bridge.")
    file_subparsers = file_parser.add_subparsers(dest="command", required=True)
    file_inspect = file_subparsers.add_parser("inspect", help="Inspect a CSV or XLSX file.")
    file_inspect.add_argument("file", help="Path to the CSV or XLSX file.")
    file_inspect.add_argument("--format", dest="format_hint", help="Optional input format hint: csv or xlsx.")
    file_inspect.add_argument("--sheet-name", help="XLSX sheet name to inspect.")
    file_inspect.add_argument("--sheet-index", type=int, default=0, help="XLSX sheet index, 0-based. Default: 0.")
    file_inspect.add_argument("--header-row", type=int, default=1, help="Physical header row number, 1-based. Default: 1.")
    file_inspect.add_argument("--max-rows", type=int, help="Maximum number of returned data rows.")
    file_inspect.add_argument("--json", action="store_true", help="Return machine-readable JSON. This is the default output mode.")

    context_parser = subparsers.add_parser("context", help="Generate a public-safe Atlas context pack.")
    context_parser.add_argument("--output", help="Optional output file path.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.group == "capability":
        return run_capability(args)
    if args.group == "project":
        return run_project(args)
    if args.group == "file":
        return run_file(args, parser)
    if args.group == "context":
        return run_context(args)

    parser.error(f"Unsupported command group: {args.group}")
    return 2


def run_capability(args: argparse.Namespace) -> int:
    if args.command == "list":
        capabilities = list_capabilities()
        if args.json:
            sys.stdout.write(json.dumps({"capabilities": capabilities}, ensure_ascii=False, indent=2))
            sys.stdout.write("\n")
            return 0
        for capability in capabilities:
            sys.stdout.write(
                f"{capability['id']}: {capability['recommendation']} | {capability['governance_status']} | {capability['use_via']}\n"
            )
        return 0

    capability = get_capability(args.capability)
    if args.json:
        sys.stdout.write(json.dumps(capability, ensure_ascii=False, indent=2))
        sys.stdout.write("\n")
        return 0

    fields = [
        ("ID", capability["id"]),
        ("Name", capability["name"]),
        ("Governance status", capability["governance_status"]),
        ("Recommendation", capability["recommendation"]),
        ("Use via", capability["use_via"]),
        ("Can use now", capability["can_use_now"]),
        ("Reference only", capability["reference_only"]),
        ("Forbidden as ready-made call", capability["forbidden_as_ready_made_call"]),
        ("Notes", capability["notes"]),
    ]
    for label, value in fields:
        sys.stdout.write(f"{label}: {value}\n")
    return 0


def run_project(args: argparse.Namespace) -> int:
    payload = inspect_project(args.project_path)
    if args.json:
        sys.stdout.write(to_json(payload))
        sys.stdout.write("\n")
        return 0

    sys.stdout.write(f"Project: {payload['project_path']}\n")
    sys.stdout.write(f"Overall recommendation: {payload['overall_recommendation']}\n")
    sys.stdout.write(f"Reason: {payload['reason']}\n")
    if not payload["findings"]:
        return 0

    for finding in payload["findings"]:
        sys.stdout.write("\n")
        sys.stdout.write(f"Capability: {finding['capability']}\n")
        sys.stdout.write(f"Detected Signal: {finding['detected_signal']}\n")
        sys.stdout.write(f"Atlas Maturity: {finding['atlas_maturity']}\n")
        sys.stdout.write(f"Recommendation: {finding['recommendation']}\n")
        sys.stdout.write(f"Reason: {finding['reason']}\n")
        sys.stdout.write(f"Confidence: {finding['confidence']}\n")
    return 0


def run_file(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    if args.sheet_name and args.sheet_index != 0:
        parser.error("--sheet-name and non-default --sheet-index cannot be used together.")
    if args.header_row < 1:
        parser.error("--header-row must be >= 1.")
    if args.max_rows is not None and args.max_rows < 1:
        parser.error("--max-rows must be >= 1.")

    result = inspect_file(
        args.file,
        format_hint=args.format_hint,
        sheet_name=args.sheet_name,
        sheet_index=args.sheet_index,
        header_row=args.header_row,
        max_rows=args.max_rows,
    )
    sys.stdout.write(json.dumps(result_to_payload(result), ensure_ascii=False, indent=2))
    sys.stdout.write("\n")
    return 0 if not result.errors else 1


def run_context(args: argparse.Namespace) -> int:
    if args.output:
        output_path = write_context(args.output)
        sys.stdout.write(f"Wrote context pack to {Path(output_path)}\n")
        return 0

    sys.stdout.write(build_context_markdown())
    sys.stdout.write("\n")
    return 0
