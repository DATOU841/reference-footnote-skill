#!/usr/bin/env python3
"""Validate returned Markdown/parsed-text grounding checks offline."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, write_json

ALLOWED = {"verified", "human_review", "failed"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--verification", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    data = read_json(args.verification)
    errors = []
    issues = []
    for item in data.get("results", []):
        status = item.get("markdown_grounding_status")
        if status not in ALLOWED:
            errors.append(f"invalid markdown_grounding_status for {item.get('insertion_id')}: {status}")
        if status in {"human_review", "failed"} or item.get("risks"):
            issues.append(item)
    out_data = {"status": "failed" if errors else "passed", "results": data.get("results", []), "issues": issues, "errors": errors}
    out = task / "state" / "markdown-verification.json"
    write_json(out, out_data)
    print_json(result(out_data["status"], output=str(out), issues=len(issues), errors=errors))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
