#!/usr/bin/env python3
"""Build an offline RAG reverse lookup request."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, search_dimensions_for_text, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--batch-id", default="batch-01")
    parser.add_argument("--priority", default="P0")
    parser.add_argument("--allow-pre-ingestion", action="store_true", help="legacy/offline fixture mode only; bypass retrieval-first intake check")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    needs_path = task / "state" / "citation-needs.json"
    if not needs_path.exists():
        print_json(result("failed", errors=["citation-needs.json missing"]))
        return 1
    intake_path = task / "state" / "intake-status.json"
    status_path = task / "state" / "status.json"
    user_declared_existing = False
    if status_path.exists():
        user_declared_existing = read_json(status_path).get("rag_library_status") == "user_declared_existing"
    if not args.allow_pre_ingestion and not user_declared_existing and not intake_path.exists():
        print_json(result("failed", errors=[
            "intake-status.json 不存在。必须先完成 A3.5 检索蓝图、A4 初始文献库建设交接、A5 入库完成应用后，才能进行 RAG 反查。",
            "若用户明确声明已有可用 RAG 文献库，请先在 startup.py 使用 --existing-rag-library。",
            "若仅为旧版离线 fixture，请使用 --allow-pre-ingestion。"
        ]))
        return 1
    needs = read_json(needs_path)
    targets = [n for n in needs["needs"] if n["need_level"] in {"critical", "important", "recommended"}]
    request = {
        "protocol_version": "1.0",
        "request_type": "reverse_lookup",
        "batch_id": args.batch_id,
        "priority": args.priority,
        "retrieval_first_status": "pre_ingestion_bypass" if args.allow_pre_ingestion else ("user_declared_existing_library" if user_declared_existing else "after_intake_completion"),
        "claims": [
            {
                "claim_id": n["claim_id"],
                "text": n["text"],
                "claim_type": n["claim_type"],
                "need_level": n["need_level"],
                "citation_type": n["citation_type"],
                "search_dimensions": search_dimensions_for_text(n["text"]),
                "context": {"section_title": n["section_title"], "article_discipline": "law"},
            }
            for n in targets
        ],
    }
    out = task / "state" / "rag-requests" / f"{args.batch_id}.json"
    write_json(out, request)
    print_json(result("passed", output=str(out), claims=len(request["claims"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
