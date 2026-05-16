#!/usr/bin/env python3
"""Install ReferenceFootnote runtime locally after review."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from reflib import ROOT, VERSION, print_json, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=["local", "staging", "production"], required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.target != "local":
        print_json(result("failed", errors=[f"{args.target} install is blocked in {VERSION}"]))
        return 2
    dest = Path.home() / ".codex" / "skills" / "参考文献补注"
    if not args.dry_run:
        if dest.exists():
            shutil.rmtree(dest)
        ignore = shutil.ignore_patterns(".git", "state", "delivery", "test-results", "__pycache__", "*.pyc")
        shutil.copytree(ROOT, dest, ignore=ignore)
    print_json(result("passed", target=args.target, copied_from=str(ROOT), copied_to=str(dest), dry_run=args.dry_run))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
