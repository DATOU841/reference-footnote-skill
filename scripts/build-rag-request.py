#!/usr/bin/env python3
"""Build an offline RAG reverse lookup request."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, search_dimensions_for_text, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--batch-id", default="batch-01")
    parser.add_argument("--priority", default="P0")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    needs_path = task / "state" / "citation-needs.json"
    if not needs_path.exists():
        print_json(result("failed", errors=["citation-needs.json missing"]))
        return 1
    needs = read_json(needs_path)
    targets = [n for n in needs["needs"] if n["need_level"] in {"critical", "important", "recommended"}]
    request = {
        "protocol_version": "1.0",
        "request_type": "reverse_lookup",
        "batch_id": args.batch_id,
        "priority": args.priority,
        "claims": [
            {
                "claim_id": n["claim_id"],
                "text": n["text"],
                "claim_type": n["claim_type"],
                "need_level": n["need_level"],
                "citation_type": n["citation_type"],
                "search_dimensions": search_dimensions_for_text(n["text"]),
                "context": {"section_title": n["section_title"], "article_discipline": "law"},
            }
            for n in targets
        ],
    }
    out = task / "state" / "rag-requests" / f"{args.batch_id}.json"
    write_json(out, request)
    print_json(result("passed", output=str(out), claims=len(request["claims"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
