#!/usr/bin/env python3
"""Validate a citation insertion plan."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, write_json


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
    metrics = {
        "critical_claim_coverage": len(critical_supported) / len(critical) if critical else 1,
        "high_risk_citation_ratio": len(high_risk) / len(plan["insertions"]) if plan["insertions"] else 0,
        "page_missing_ratio": len(page_missing) / len(plan["insertions"]) if plan["insertions"] else 0,
    }
    blocking = []
    warnings = []
    if metrics["critical_claim_coverage"] < 0.8:
        blocking.append("critical claim coverage below 80%")
    if metrics["high_risk_citation_ratio"] > 0.2:
        warnings.append("high-risk citation ratio above 20%")
    if metrics["page_missing_ratio"] > 0.3:
        warnings.append("page missing ratio above 30%")
    status = "failed" if blocking else "passed"
    report = {"status": status, "blocking_issues": blocking, "warnings": warnings, "metrics": metrics}
    out = task / "state" / "quality-report.json"
    write_json(out, report)
    print_json(result(status if not (status == "failed" and args.allow_fail) else "passed", output=str(out), report=report))
    return 0 if status == "passed" or args.allow_fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
