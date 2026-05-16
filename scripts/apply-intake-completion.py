#!/usr/bin/env python3
"""Apply a synthetic search-intake completion payload."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--completion", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    completion = read_json(args.completion)
    errors = []
    if completion.get("status") not in {"completed", "partial", "failed"}:
        errors.append("completion status must be completed, partial, or failed")
    if not completion.get("handoff_id"):
        errors.append("handoff_id missing")
    out = task / "state" / "intake-status.json"
    write_json(out, completion)
    print_json(result("failed" if errors else "passed", output=str(out), errors=errors))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
