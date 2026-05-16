#!/usr/bin/env python3
"""Print current offline task status."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ROOT, print_json, read_json, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", type=Path, default=ROOT)
    args = parser.parse_args()
    status = args.task_dir / "state" / "status.json"
    if not status.exists():
        print_json(result("failed", errors=["state/status.json missing"]))
        return 1
    print_json(read_json(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
