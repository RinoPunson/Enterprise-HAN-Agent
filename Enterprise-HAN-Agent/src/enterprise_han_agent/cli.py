"""Command-line entry point for Enterprise-HAN-Agent."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .pipeline import EnterpriseHANPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run HAN-inspired enterprise risk analysis.")
    parser.add_argument("text", nargs="?", help="Input enterprise event text. Omit when using --input.")
    parser.add_argument("-i", "--input", type=Path, help="Path to a UTF-8 text file.")
    parser.add_argument("-t", "--target-company", help="Preferred target company name.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.input:
        text = args.input.read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read()

    if not text.strip():
        parser.error("input text is required")

    pipeline = EnterpriseHANPipeline()
    result = pipeline.analyze(text, target_company=args.target_company)
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

