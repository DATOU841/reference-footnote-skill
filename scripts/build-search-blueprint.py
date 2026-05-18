#!/usr/bin/env python3
"""Build article-level retrieval directions before reference selection."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, search_dimensions_for_text, write_json


TYPE_COVERAGE_TARGETS = {
    "journal_article": ">=12",
    "monograph_chapter": ">=5",
    "policy_document": ">=5",
    "primary_source": ">=3",
    "english_article": ">=5",
    "patent_or_standard": "按需",
    "classic_foundational": ">=3",
}


def dedupe(items: list[str], limit: int = 20) -> list[str]:
    seen = set()
    out = []
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
        if len(out) >= limit:
            break
    return out


def bucket_name(need: dict) -> str:
    ctype = need.get("claim_type")
    citation_type = need.get("citation_type")
    if citation_type == "empirical" or ctype in {"factual_claim", "data_judgment"}:
        return "事实材料与实证研究"
    if ctype in {"theoretical_claim", "definition"}:
        return "概念理论与核心范畴"
    if ctype == "policy_judgment":
        return "政策制度与实践对策"
    return "学术争议与背景综述"


def source_types_for(need: dict) -> list[str]:
    ctype = need.get("claim_type")
    citation_type = need.get("citation_type")
    if citation_type == "empirical" or ctype in {"factual_claim", "data_judgment"}:
        return ["journal_article", "primary_source", "policy_document"]
    if ctype in {"theoretical_claim", "definition"}:
        return ["journal_article", "monograph_chapter", "classic_foundational", "english_article"]
    if ctype == "policy_judgment":
        return ["policy_document", "journal_article", "primary_source"]
    return ["journal_article", "monograph_chapter", "english_article"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--target-references", type=int, default=30)
    parser.add_argument("--initial-pool-min", type=int, default=40)
    parser.add_argument("--min-usable-text-avg", type=int, default=200)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    needs_path = task / "state" / "citation-needs.json"
    article_path = task / "state" / "article-structure.json"
    if not needs_path.exists() or not article_path.exists():
        print_json(result("failed", errors=["article-structure.json or citation-needs.json missing"]))
        return 1
    needs = read_json(needs_path)
    article = read_json(article_path)
    targets = [n for n in needs.get("needs", []) if n.get("need_level") in {"critical", "important", "recommended"}]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for need in targets:
        grouped[bucket_name(need)].append(need)
    directions = []
    for idx, (name, items) in enumerate(grouped.items(), start=1):
        zh_terms = []
        en_terms = []
        theory_terms = []
        source_types = []
        claim_ids = []
        for item in items:
            dims = search_dimensions_for_text(item.get("text", ""))
            zh_terms.extend(dims.get("keyword", {}).get("terms", []))
            en_terms.extend(dims.get("keyword_en", {}).get("terms", []))
            theory_terms.extend(dims.get("theory", {}).get("terms", []))
            source_types.extend(source_types_for(item))
            claim_ids.append(item.get("claim_id"))
        priority = "P0" if any(item.get("need_level") == "critical" for item in items) else "P1"
        directions.append({
            "direction_id": f"dir-{idx:03d}",
            "name": name,
            "priority": priority,
            "claim_ids": claim_ids,
            "claim_count": len(items),
            "keywords_zh": dedupe(zh_terms) or dedupe([item.get("text", "")[:12] for item in items]),
            "keywords_en": dedupe(en_terms),
            "theory_hints": dedupe(theory_terms),
            "source_types": dedupe(source_types),
            "minimum_sources": 5 if priority == "P0" else 3,
            "ideal_sources": 8 if priority == "P0" else 5,
            "purpose": "先形成足量可 RAG 反查的文献库，再由 ReferenceFootnote 对比证据并筛选脚注/参考文献。",
        })
    blueprint = {
        "article_id": needs.get("article_id"),
        "article_title": article.get("title"),
        "workflow_rule": "retrieval_first",
        "must_build_library_before_reference_selection": True,
        "target_reference_count": args.target_references,
        "initial_pool_min_sources": args.initial_pool_min,
        "min_usable_text_avg_per_source": args.min_usable_text_avg,
        "type_coverage_minimum": 3,
        "type_coverage_targets": TYPE_COVERAGE_TARGETS,
        "directions": directions,
        "quality_floor": {
            "requires_search_intake_call": True,
            "requires_intake_completion_before_rag": True,
            "requires_post_ingestion_rag_before_reference_plan": True,
            "type_coverage_minimum": 3,
        },
    }
    out = task / "state" / "search-blueprint.json"
    write_json(out, blueprint)
    print_json(result("passed", output=str(out), directions=len(directions), initial_pool_min_sources=args.initial_pool_min))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
