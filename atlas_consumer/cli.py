from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .bridge import inspect_file, result_to_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m atlas_consumer",
        description="Read CSV/XLSX through Atlas Tabular Core and return structured JSON.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect a CSV or XLSX file through Atlas Tabular Core.",
    )
    inspect_parser.add_argument("file", help="Path to the CSV or XLSX file.")
    inspect_parser.add_argument("--format", dest="format_hint", help="Optional input format hint: csv or xlsx.")
    inspect_parser.add_argument("--sheet-name", help="XLSX sheet name to inspect.")
    inspect_parser.add_argument("--sheet-index", type=int, default=0, help="XLSX sheet index, 0-based. Default: 0.")
    inspect_parser.add_argument("--header-row", type=int, default=1, help="Physical header row number, 1-based. Default: 1.")
    inspect_parser.add_argument("--max-rows", type=int, help="Maximum number of returned data rows.")
    inspect_parser.add_argument(
        "--output-json",
        nargs="?",
        const="-",
        default="-",
        help="Write JSON to a file path, or use stdout when omitted or '-'.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "inspect":
        parser.error(f"Unsupported command: {args.command}")

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
    json_text = result_to_json(result)

    output_json = args.output_json
    if output_json in (None, "-"):
        sys.stdout.write(json_text)
        sys.stdout.write("\n")
    else:
        output_path = Path(output_json)
        output_path.write_text(json_text, encoding="utf-8")
        sys.stdout.write(f"Wrote JSON to {output_path}\n")

    return 0 if not result.errors else 1
