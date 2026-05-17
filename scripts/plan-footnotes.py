#!/usr/bin/env python3
"""Plan footnote and reference insertions from the evidence map."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import PROTECTED_TYPES, consumption_depth_for_strength, ensure_task, infer_evidence_type, infer_source_role, print_json, read_json, result, write_json


def footnote_text(ref: dict, style: str = "chinese_legal_journal") -> str:
    authors = "、".join(ref.get("authors", ["佚名"]))
    title = ref.get("title", "未题名文献")
    source = ref.get("source", "")
    year = ref.get("year", "")
    pages = ref.get("pages", "")
    if style in {"gb_t_7714", "gbt7714"}:
        return f"{authors}. {title}[J]. {source}, {year}: {pages}."
    return f"参见{authors}：《{title}》，载《{source}》{year}年，第{pages}页。"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--style", default="chinese_legal_journal")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    evidence_path = task / "state" / "evidence-map.json"
    if not evidence_path.exists():
        print_json(result("failed", errors=["evidence-map.json missing"]))
        return 1
    evidence = read_json(evidence_path)
    insertions = []
    no_insert = []
    refs = {}
    for entry in evidence["claim_evidence"]:
        if entry["claim_type"] in PROTECTED_TYPES or entry["evidence_status"] in {"no_support", "conflict", "not_needed"}:
            if entry["claim_type"] in PROTECTED_TYPES or entry["evidence_status"] in {"no_support", "conflict"}:
                no_insert.append({
                    "claim_id": entry["claim_id"],
                    "text": entry["text"],
                    "reason": f"{entry['claim_type']} / {entry['evidence_status']}",
                    "no_insert_reason": f"{entry['claim_type']} / {entry['evidence_status']}",
                    "writer_action": "标注为作者观点或人工复核，不得自动补注",
                    "rewrite_suggestion": None if entry["claim_type"] in PROTECTED_TYPES else "建议降低论断强度或补充来源后再处理。",
                })
            continue
        if entry["evidence_status"] in {"strong_support", "partial_support"} and entry.get("candidates"):
            cand = entry["candidates"][0]
            ref = cand.get("reference", {})
            ref_id = ref.get("ref_id", cand.get("candidate_id"))
            refs[ref_id] = ref
            risks = cand.get("risks", [])
            gbt = footnote_text(ref, "gb_t_7714")
            insertions.append({
                "insertion_id": f"ins-{len(insertions)+1:03d}",
                "claim_id": entry["claim_id"],
                "claim_type": entry["claim_type"],
                "need_level": entry["need_level"],
                "evidence_type": infer_evidence_type(entry["claim_type"], ref),
                "source_role": infer_source_role(entry["claim_type"], entry.get("citation_type")),
                "consumption_depth_suggestion": consumption_depth_for_strength(entry["evidence_status"], risks),
                "target_location": {"paragraph_id": entry["paragraph_id"], "sentence_id": entry["source_sentence_id"]},
                "footnote_content": {"style": args.style, "text": footnote_text(ref, args.style), "gbt7714_footnote": gbt},
                "gbt7714_footnote": gbt,
                "evidence_basis": {
                    "support_strength": entry["evidence_status"],
                    "confidence": cand.get("support_assessment", {}).get("confidence", 0),
                    "risks": risks,
                    "source_ref_id": ref_id,
                },
                "requires_rewrite": entry["evidence_status"] == "partial_support" or bool(risks),
                "rewrite_suggestion": "建议限定表述或人工确认页码。" if entry["evidence_status"] == "partial_support" or risks else None,
            })
    plan = {
        "article_id": evidence["article_id"],
        "style": args.style,
        "insertions": insertions,
        "no_insert_zones": no_insert,
        "reference_list": {"new_references": list(refs.values()), "existing_references_verified": []},
    }
    out = task / "state" / "insertion-plan.json"
    write_json(out, plan)
    print_json(result("passed", output=str(out), insertions=len(insertions), no_insert_zones=len(no_insert)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
