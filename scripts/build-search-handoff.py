#!/usr/bin/env python3
"""Build a search-intake gap handoff without executing search."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, write_json


def terms(dimensions: dict, key: str, field: str = "terms") -> list[str]:
    value = dimensions.get(key, {})
    if isinstance(value, dict):
        raw = value.get(field, [])
        return raw if isinstance(raw, list) else []
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--batch-id", default="gap-round2")
    parser.add_argument("--priority", default="P0")
    parser.add_argument("--macro-round", default="round2")
    parser.add_argument("--request-type", default="search_intake_gap")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    evidence_path = task / "state" / "evidence-map.json"
    if not evidence_path.exists():
        print_json(result("failed", errors=["evidence-map.json missing"]))
        return 1
    evidence = read_json(evidence_path)
    gaps = evidence.get("critical_gaps", [])
    requests = []
    for gap in gaps:
        dims = gap.get("search_dimensions", {})
        keywords_zh = terms(dims, "keyword") or [gap["text"][:12]]
        requests.append({
            "request_id": f"si-{gap['claim_id']}",
            "macro_round": args.macro_round,
            "gap_id": f"gap-{gap['claim_id']}",
            "claim_id": gap["claim_id"],
            "claim_text": gap["text"],
            "claim_type": gap["claim_type"],
            "need_level": gap["need_level"],
            "source_need": gap.get("citation_type", "secondary_source"),
            "priority": args.priority,
            "source_direction": f"{gap['section_title']}：围绕{', '.join(keywords_zh)}补充直接支撑来源",
            "purpose": f"支撑{gap['claim_type']}中的{gap['need_level']}引用需求",
            "minimum_requirement": "至少1篇可直接支撑文献，并尽量包含可核验页码",
            "ideal_requirement": "2-3篇不同角度支撑文献，优先含期刊论文、权威专著或一手材料",
            "search_strategy": {
                "keywords_zh": keywords_zh,
                "keywords_en": terms(dims, "keyword_en"),
                "author_hints": terms(dims, "author", "names"),
                "theory_hints": terms(dims, "theory"),
                "databases": ["CNKI", "WoS"],
                "source_types": ["journal_article", "monograph"],
                "discipline": "law",
                "constraints": {
                    "gap_driven_only": True,
                    "no_general_pool_expansion": True,
                    "requires_pdf_when_available": True,
                    "target_kb": "B" if args.macro_round == "round1" else "C",
                },
            },
        })
    handoff = {
        "protocol_version": "1.1",
        "request_type": args.request_type,
        "source_skill": "参考文献补注",
        "target_skill": "检索入库",
        "staging_status": "blocked",
        "handoff_id": f"search-handoff-{args.batch_id}",
        "batch_id": args.batch_id,
        "macro_round": args.macro_round,
        "priority": args.priority,
        "retrieval_first": False,
        "gap_driven": True,
        "requests": requests,
    }
    out = task / "state" / "search-intake-requests" / f"{args.batch_id}.json"
    write_json(out, handoff)
    print_json(result("passed", output=str(out), requests=len(handoff["requests"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
