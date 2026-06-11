#!/usr/bin/env python3
"""Build post-ingestion RAG reverse-lookup metadata for the executor."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, search_dimensions_for_text, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--batch-id", default="post-ingestion-01")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    completion_path = task / "state" / "intake-status.json"
    needs_path = task / "state" / "citation-needs.json"
    if not completion_path.exists():
        print_json(result("failed", errors=["intake-status.json missing"]))
        return 1
    if not needs_path.exists():
        print_json(result("failed", errors=["citation-needs.json missing"]))
        return 1
    completion = read_json(completion_path)
    needs = {item["claim_id"]: item for item in read_json(needs_path).get("needs", [])}
    targets = []
    for item in completion.get("results", []):
        import_status = item.get("import_status", {})
        if not import_status.get("rag_indexed"):
            continue
        claim = needs.get(item.get("claim_id"))
        if not claim:
            continue
        targets.append({
            "claim_id": claim["claim_id"],
            "text": claim["text"],
            "claim_type": claim["claim_type"],
            "need_level": claim["need_level"],
            "citation_type": claim["citation_type"],
            "search_dimensions": search_dimensions_for_text(claim["text"]),
            "kb_routing": item.get("kb_routing", {}),
            "ref_metadata": item.get("ref_metadata"),
            "zotero_id": item.get("zotero_id"),
        })
    errors = []
    if not targets:
        errors.append("no rag-indexed intake results available for post-ingestion lookup")
    package = {
        "protocol_version": "1.0",
        "call_type": "rag_reverse_lookup_after_ingestion",
        "batch_id": args.batch_id,
        "source_skill": "参考文献补注",
        "target_system": "RAG platform",
        "execution_status": "ready_for_referencefootnote_executor",
        "executor_script": "scripts/run-rag-reverse-lookup.py",
        "input_completion_id": completion.get("completion_id"),
        "claims": targets,
        "return_contract": {
            "response_type": "reverse_lookup_result",
            "required_fields": ["batch_id", "results[].claim_id", "results[].candidates", "support_assessment", "match_details.snippet_page"],
            "risk_policy": "page_missing, ocr_uncertain, secondhand_citation, concept_approximate, temporal_mismatch, discipline_cross, translation_gap must be preserved",
        },
        "errors": errors,
    }
    out_dir = task / "state" / "rag-calls"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{args.batch_id}.json"
    write_json(out, package)
    print_json(result("failed" if errors else "passed", output=str(out), claims=len(targets), errors=errors))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
