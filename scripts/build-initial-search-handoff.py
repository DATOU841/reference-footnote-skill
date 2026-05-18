#!/usr/bin/env python3
"""Build an initial library-building handoff for 检索入库."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--batch-id", default="initial-library")
    parser.add_argument("--macro-round", default="round1")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    blueprint_path = task / "state" / "search-blueprint.json"
    if not blueprint_path.exists():
        print_json(result("failed", errors=["search-blueprint.json missing"]))
        return 1
    blueprint = read_json(blueprint_path)
    requests = []
    for direction in blueprint.get("directions", []):
        requests.append({
            "request_id": f"lib-{direction['direction_id']}",
            "macro_round": args.macro_round,
            "gap_id": None,
            "claim_id": None,
            "claim_ids": direction.get("claim_ids", []),
            "claim_text": None,
            "claim_type": "article_level_retrieval_direction",
            "need_level": "library_build",
            "source_need": "mixed_scholarly_sources",
            "priority": direction.get("priority", "P1"),
            "source_direction": direction["name"],
            "purpose": direction.get("purpose", "建设足量文献库供 RAG 反查和脚注筛选。"),
            "minimum_requirement": f"本方向至少入库 {direction.get('minimum_sources', 3)} 篇可 RAG 消费文献，每篇尽量提供正文级可消费材料。",
            "ideal_requirement": f"本方向理想入库 {direction.get('ideal_sources', 5)} 篇，全文初始文献池不少于 {blueprint.get('initial_pool_min_sources', 40)} 篇。",
            "search_strategy": {
                "keywords_zh": direction.get("keywords_zh", []),
                "keywords_en": direction.get("keywords_en", []),
                "author_hints": [],
                "theory_hints": direction.get("theory_hints", []),
                "databases": ["CNKI", "WoS"],
                "source_types": direction.get("source_types", []),
                "discipline": "article_inferred",
                "constraints": {
                    "library_build_before_rag": True,
                    "no_reference_selection_before_ingestion": True,
                    "requires_pdf_when_available": True,
                    "min_usable_text_avg_per_source": blueprint.get("min_usable_text_avg_per_source", 200),
                    "target_kb": "B" if args.macro_round == "round1" else "C",
                },
            },
        })
    handoff = {
        "protocol_version": "1.1",
        "request_type": "search_intake_library_build",
        "source_skill": "参考文献补注",
        "target_skill": "检索入库",
        "staging_status": "blocked",
        "handoff_id": f"search-handoff-{args.batch_id}",
        "batch_id": args.batch_id,
        "macro_round": args.macro_round,
        "priority": "P0",
        "retrieval_first": True,
        "library_requirements": {
            "target_reference_count": blueprint.get("target_reference_count", 30),
            "initial_pool_min_sources": blueprint.get("initial_pool_min_sources", 40),
            "min_usable_text_avg_per_source": blueprint.get("min_usable_text_avg_per_source", 200),
            "type_coverage_minimum": blueprint.get("type_coverage_minimum", 3),
            "type_coverage_targets": blueprint.get("type_coverage_targets", {}),
            "post_ingestion_rag_required": True,
        },
        "requests": requests,
    }
    out = task / "state" / "search-intake-requests" / f"{args.batch_id}.json"
    write_json(out, handoff)
    print_json(result("passed", output=str(out), requests=len(requests), request_type=handoff["request_type"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
