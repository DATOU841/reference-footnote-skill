#!/usr/bin/env python3
"""Diagnose citation needs for segmented claims."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import diagnose_need, ensure_task, print_json, read_json, result, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    claims_path = task / "state" / "claim-segments.json"
    if not claims_path.exists():
        print_json(result("failed", errors=["claim-segments.json missing"]))
        return 1
    claims = read_json(claims_path)
    needs = []
    for claim in claims["claims"]:
        level, ctype = diagnose_need(claim["claim_type"], claim["text"])
        needs.append({**claim, "need_level": level, "citation_type": ctype})
    out_data = {"article_id": claims["article_id"], "needs": needs}
    out = task / "state" / "citation-needs.json"
    write_json(out, out_data)
    print_json(result("passed", output=str(out), needs=len(needs)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
