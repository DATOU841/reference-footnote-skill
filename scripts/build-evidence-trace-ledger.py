#!/usr/bin/env python3
"""Build the full-order evidence trace ledger."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, update_flow_status, write_json


def load_interpretations(task: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted((task / "state" / "evidence-interpretations").glob("*.json")):
        data = read_json(path)
        batch_id = data.get("batch_id", path.stem)
        for interp in data.get("interpretations", []):
            claim_id = interp.get("claim_id")
            if claim_id:
                out[claim_id] = {**interp, "batch_id": batch_id}
    return out


def load_grounding(task: Path) -> dict[tuple[str, str], dict]:
    path = task / "state" / "grounding-resolution.json"
    if not path.exists():
        return {}
    data = read_json(path)
    out = {}
    for item in data.get("resolved_items", []):
        out[(item.get("claim_id"), item.get("candidate_id"))] = item
    return out


def load_insertions(task: Path) -> dict[str, dict]:
    for name in ["cleaned-insertion-plan.json", "insertion-plan.json"]:
        path = task / "state" / name
        if path.exists():
            plan = read_json(path)
            return {item.get("claim_id"): item for item in plan.get("insertions", [])}
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    needs_path = task / "state" / "citation-needs.json"
    if not needs_path.exists():
        print_json(result("failed", errors=["citation-needs.json missing"]))
        return 1
    needs = read_json(needs_path)
    interpretations = load_interpretations(task)
    grounding = load_grounding(task)
    insertions = load_insertions(task)
    entries = []
    for order, need in enumerate(needs.get("needs", []), start=1):
        claim_id = need.get("claim_id")
        interp = interpretations.get(claim_id, {})
        candidate = (interp.get("candidates") or [{}])[0] if interp.get("candidates") else {}
        cand_id = candidate.get("candidate_id")
        ground = grounding.get((claim_id, cand_id), {})
        assessment = candidate.get("support_assessment", {}) or {}
        ref = candidate.get("reference", {}) or {}
        ins = insertions.get(claim_id, {})
        risks = list(dict.fromkeys(
            (interp.get("risks") or []) +
            (candidate.get("risks") or []) +
            (ground.get("risk_flags") or []) +
            (ins.get("evidence_basis", {}).get("risks", []) if ins else [])
        ))
        support = assessment.get("strength") or interp.get("best_strength")
        final = "pending"
        if need.get("need_level") == "not_needed":
            final = "no_note_needed"
        elif support in {"no_support", "no_support_found", None} and need.get("need_level") in {"critical", "important"}:
            final = "needs_gap_handoff"
        if ins:
            final = "inserted"
        entries.append({
            "order": order,
            "paragraph_id": need.get("paragraph_id"),
            "sentence_id": need.get("source_sentence_id"),
            "claim_id": claim_id,
            "original_text": need.get("text"),
            "citation_need": need.get("need_level"),
            "citation_type": need.get("citation_type"),
            "claim_type": need.get("claim_type"),
            "rag_query": need.get("text") if need.get("need_level") != "not_needed" else None,
            "rag_result_id": f"{interp.get('batch_id')}:{claim_id}" if interp else None,
            "retrieved_chunk_id": candidate.get("chunk_id") or candidate.get("retrieved_chunk_id"),
            "source_ref_id": ref.get("ref_id") or candidate.get("source_ref_id"),
            "support_strength": support,
            "grounding_status": ground.get("grounding_status") or ins.get("grounding_status"),
            "note_id": ins.get("insertion_id"),
            "note_text": ins.get("footnote_content", {}).get("text"),
            "reference_id": ins.get("evidence_basis", {}).get("source_ref_id") or ref.get("ref_id"),
            "risk_flags": risks,
            "writing_pool_decision": None,
            "cleanup_status": "not_started" if risks or ins else "not_applicable",
            "final_decision": final,
        })
    ledger = {
        "version": "0.5.2-dev",
        "article_id": needs.get("article_id"),
        "total_entries": len(entries),
        "entries": entries,
    }
    out = task / "state" / "evidence-trace-ledger.json"
    write_json(out, ledger)
    update_flow_status(task, "S60", note=f"evidence trace entries={len(entries)}")
    print_json(result("passed", output=str(out), entries=len(entries)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
