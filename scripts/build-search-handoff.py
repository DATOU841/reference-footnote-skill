#!/usr/bin/env python3
"""Build a search-intake gap handoff without executing search."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--batch-id", default="batch-01")
    parser.add_argument("--priority", default="P0")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    evidence_path = task / "state" / "evidence-map.json"
    if not evidence_path.exists():
        print_json(result("failed", errors=["evidence-map.json missing"]))
        return 1
    evidence = read_json(evidence_path)
    gaps = evidence.get("critical_gaps", [])
    handoff = {
        "protocol_version": "1.0",
        "request_type": "search_intake_gap",
        "source_skill": "参考文献补注",
        "target_skill": "检索入库",
        "staging_status": "blocked",
        "handoff_id": f"search-handoff-{args.batch_id}",
        "batch_id": args.batch_id,
        "priority": args.priority,
        "requests": [
            {
                "request_id": f"si-{gap['claim_id']}",
                "claim_id": gap["claim_id"],
                "claim_text": gap["text"],
                "purpose": f"支撑{gap['claim_type']}中的{gap['need_level']}引用需求",
                "minimum_requirement": "至少1篇可直接支撑文献",
                "ideal_requirement": "2-3篇不同角度支撑文献",
                "search_strategy": {
                    "keywords_zh": [term for term in ["平台", "规则", "比例原则", "自动化审核", "申诉", "透明度", "产权"] if term in gap["text"]],
                    "databases": ["CNKI", "WoS"],
                    "source_types": ["journal_article", "monograph"],
                    "discipline": "law",
                },
            }
            for gap in gaps
        ],
    }
    out = task / "state" / "search-intake-requests" / f"{args.batch_id}.json"
    write_json(out, handoff)
    print_json(result("passed", output=str(out), requests=len(handoff["requests"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
