#!/usr/bin/env python3
"""Validate a citation insertion plan."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, write_json

ALLOWED_EVIDENCE_SOURCES = {"rag_verified", "intake_completed", "user_declared_existing", None}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--allow-fail", action="store_true")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    plan_path = task / "state" / "insertion-plan.json"
    evidence_path = task / "state" / "evidence-map.json"
    if not plan_path.exists() or not evidence_path.exists():
        print_json(result("failed", errors=["insertion-plan.json or evidence-map.json missing"]))
        return 1
    plan = read_json(plan_path)
    evidence = read_json(evidence_path)
    critical = [c for c in evidence["claim_evidence"] if c["need_level"] == "critical"]
    critical_supported = [c for c in critical if c["evidence_status"] in {"strong_support", "partial_support"}]
    high_risk = [ins for ins in plan["insertions"] if ins["evidence_basis"].get("risks")]
    page_missing = [ins for ins in high_risk if "page_missing" in ins["evidence_basis"].get("risks", [])]
    footnote_like = [ins for ins in plan["insertions"] if ins.get("note_type", "footnote") in {"footnote", "endnote"}]
    references = plan.get("reference_list", {}).get("new_references", [])
    intake_path = task / "state" / "intake-status.json"
    intake = read_json(intake_path) if intake_path.exists() else {}
    blueprint_path = task / "state" / "search-blueprint.json"
    initial_handoff = task / "state" / "search-intake-requests" / "initial-library.json"
    status_path = task / "state" / "status.json"
    user_declared_existing = status_path.exists() and read_json(status_path).get("rag_library_status") == "user_declared_existing"
    intake_gate_path = task / "state" / "intake-quality-gate.json"
    metrics = {
        "critical_claim_coverage": len(critical_supported) / len(critical) if critical else 1,
        "high_risk_citation_ratio": len(high_risk) / len(plan["insertions"]) if plan["insertions"] else 0,
        "page_missing_ratio": len(page_missing) / len(plan["insertions"]) if plan["insertions"] else 0,
        "footnote_count": len(footnote_like),
        "reference_count": len(references),
        "pool_avg_usable_text_chars": intake.get("pool_avg_usable_text_chars"),
        "pool_material_status": intake.get("pool_material_status", "not_reported"),
        "retrieval_first_ready": user_declared_existing or (blueprint_path.exists() and initial_handoff.exists() and intake_path.exists()),
        "library_provenance": "user_declared_not_skill_built" if user_declared_existing else "skill_built_or_required",
    }
    blocking = []
    warnings = []
    if metrics["critical_claim_coverage"] < 0.8:
        blocking.append("critical claim coverage below 80%")
    if metrics["high_risk_citation_ratio"] > 0.2:
        warnings.append("high-risk citation ratio above 20%")
    if metrics["page_missing_ratio"] > 0.3:
        warnings.append("page missing ratio above 30%")
    if metrics["footnote_count"] < 10:
        warnings.append("footnote count below expected 10-20 range")
    if metrics["footnote_count"] > 20:
        blocking.append("footnote count above 20; prune unnecessary notes")
    if metrics["reference_count"] < 20:
        warnings.append("reference count below expected 25-30 range")
    if metrics["reference_count"] > 35:
        warnings.append("reference count above 35; prune weak or unconsumed references")
    if metrics["reference_count"] > 40:
        blocking.append("reference count above 40")
    if metrics["pool_material_status"] == "insufficient":
        warnings.append("average usable text below 200 chars per source pool")
    if not user_declared_existing and not blueprint_path.exists():
        blocking.append("retrieval blueprint missing; 必须先完成文章反推检索蓝图 (A3.5)")
    elif user_declared_existing and not blueprint_path.exists():
        warnings.append("retrieval blueprint missing because user declared existing RAG library")
    if not user_declared_existing and not initial_handoff.exists():
        blocking.append("initial library search handoff missing; 必须先完成初始文献库建设交接 (A4)")
    elif user_declared_existing and not initial_handoff.exists():
        warnings.append("initial library handoff missing because user declared existing RAG library")
    if not user_declared_existing and not intake_path.exists():
        blocking.append("intake completion missing before citation plan")
    if intake_gate_path.exists():
        intake_gate = read_json(intake_gate_path)
        if intake_gate.get("status") == "failed":
            warnings.append("入库质量验收未通过; 参考文献池可能不足")
    elif not user_declared_existing:
        warnings.append("intake-quality-gate.json missing")
    for ins in plan["insertions"]:
        if ins.get("annotation_purpose") == "reference_only" and ins.get("note_type") in {"footnote", "endnote"}:
            blocking.append(f"{ins.get('insertion_id')} reference_only cannot enter footnote/endnote body")
        source = ins.get("evidence_basis", {}).get("evidence_source")
        if source not in ALLOWED_EVIDENCE_SOURCES:
            blocking.append(f"{ins.get('insertion_id')} invalid evidence_source: {source}")
    status = "failed" if blocking else "passed"
    report = {"status": status, "blocking_issues": blocking, "warnings": warnings, "metrics": metrics}
    out = task / "state" / "quality-report.json"
    write_json(out, report)
    print_json(result(status if not (status == "failed" and args.allow_fail) else "passed", output=str(out), report=report))
    return 0 if status == "passed" or args.allow_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
