#!/usr/bin/env python3
"""Export a full-order audit from the evidence trace ledger."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, update_flow_status, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    ledger_path = task / "state" / "evidence-trace-ledger.json"
    if not ledger_path.exists():
        print_json(result("failed", errors=["evidence-trace-ledger.json missing"]))
        return 1
    ledger = read_json(ledger_path)
    rows = []
    blocking = []
    for entry in ledger.get("entries", []):
        judgment = "无需注释" if entry.get("final_decision") == "no_note_needed" else "待处理"
        if entry.get("final_decision") == "inserted":
            judgment = "可保留"
        elif entry.get("final_decision") == "deleted_by_cleanup":
            judgment = "已清理删除"
        elif entry.get("final_decision") == "downgraded_by_cleanup":
            judgment = "已降级保留/待人工确认"
        elif entry.get("final_decision") == "blocked_rewrite_required":
            judgment = "阻断：需完整段落重写"
            blocking.append(entry.get("claim_id"))
        rows.append({
            "order": entry.get("order"),
            "paragraph_id": entry.get("paragraph_id"),
            "sentence_id": entry.get("sentence_id"),
            "claim_id": entry.get("claim_id"),
            "original_text": entry.get("original_text"),
            "note_id": entry.get("note_id"),
            "support_strength": entry.get("support_strength"),
            "grounding_status": entry.get("grounding_status"),
            "risk_flags": entry.get("risk_flags", []),
            "cleanup_status": entry.get("cleanup_status"),
            "final_decision": entry.get("final_decision"),
            "judgment": judgment,
        })
    audit = {"status": "failed" if blocking else "passed", "blocking_claims": blocking, "items": rows}
    out = task / "state" / "full-order-audit.json"
    write_json(out, audit)
    md_lines = ["# 全文顺序逐条核查清单", "", "| 顺序 | claim | 注释 | 支撑 | 风险 | 结论 |", "| --- | --- | --- | --- | --- | --- |"]
    for row in rows:
        md_lines.append(f"| {row['order']} | {row['claim_id']} | {row.get('note_id') or ''} | {row.get('support_strength') or ''} | {', '.join(row.get('risk_flags') or [])} | {row['judgment']} |")
    (task / "state" / "full-order-audit.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    update_flow_status(task, "S105", blocked=bool(blocking), note=f"audit blocking={len(blocking)}")
    print_json(result(audit["status"], output=str(out), items=len(rows), blocking=len(blocking)))
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
