#!/usr/bin/env python3
"""Update evidence trace ledger from a risk-cleanup result."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from reflib import ROOT


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--cleanup-result", type=Path)
    args = parser.parse_args()
    cmd = ["python3", str(ROOT / "scripts" / "apply-risk-cleanup-result.py"), "--task-dir", str(args.task_dir)]
    if args.cleanup_result:
        cmd.extend(["--cleanup-result", str(args.cleanup_result)])
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
