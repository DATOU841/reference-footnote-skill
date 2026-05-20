#!/usr/bin/env python3
"""Update/rebuild the evidence trace ledger after RAG interpretation."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from reflib import ROOT


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    args = parser.parse_args()
    return subprocess.call(["python3", str(ROOT / "scripts" / "build-evidence-trace-ledger.py"), "--task-dir", str(args.task_dir)], cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
