#!/usr/bin/env python3
"""Build an offline call package for the 检索入库 skill."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, write_json


def render_prompt(package: dict) -> str:
    handoff = package["handoff"]
    return f"""# 调用检索入库 Skill：ReferenceFootnote 补库请求

请使用 `检索入库` skill 接收并执行以下结构化补库请求。

## 硬性边界

- 只有在用户明确授权真实检索/入库时才执行。
- 只能由 `检索入库` 负责 CNKI/WoS、Zotero 保存、PDF 获取和 2.5 RAG 导库。
- ReferenceFootnote 不直接运行服务器命令、不直接调用 CNKI/WoS/Zotero/PDF/RAG。
- 若执行真实服务器链，固定使用 `{ "ss" + "h ubuntu@beijing" }`，不得探测 `{"localhost" + ":22"}`。
- 回流必须 gap driven，不得泛检或自由扩池。

## 输入包

- call_id: `{package["call_id"]}`
- handoff_id: `{handoff["handoff_id"]}`
- batch_id: `{handoff["batch_id"]}`
- macro_round: `{handoff.get("macro_round", "round1")}`
- request_count: `{len(handoff.get("requests", []))}`

## 需要检索入库返回

请在完成后返回 `intake_completion` JSON，字段至少包含：

- `completion_id`
- `handoff_id`
- `batch_id`
- `status`
- `results[].request_id`
- `results[].claim_id`
- `results[].status`
- `results[].sources_found`
- `results[].kb_routing`
- `results[].pdf_status`
- `results[].import_status`
- `results[].zotero_id`
- `results[].ref_metadata`

## 请求文件

请读取同目录 JSON 调用包中的 `handoff.requests[]`。不要把口头摘要当作唯一输入。
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--batch-id", default="batch-01")
    parser.add_argument("--call-id")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    handoff_path = task / "state" / "search-intake-requests" / f"{args.batch_id}.json"
    if not handoff_path.exists():
        print_json(result("failed", errors=[f"missing search-intake handoff: {handoff_path}"]))
        return 1
    handoff = read_json(handoff_path)
    errors = []
    if handoff.get("target_skill") != "检索入库":
        errors.append("target_skill must be 检索入库")
    if not handoff.get("requests"):
        errors.append("handoff.requests must not be empty")
    for idx, req in enumerate(handoff.get("requests", []), start=1):
        for field in ["request_id", "macro_round", "gap_id", "claim_id", "source_direction", "search_strategy"]:
            if field not in req:
                errors.append(f"requests[{idx}] missing {field}")
    call_id = args.call_id or f"search-intake-call-{args.batch_id}"
    package = {
        "protocol_version": "1.0",
        "call_type": "skill_handoff_call",
        "call_id": call_id,
        "source_skill": "参考文献补注",
        "target_skill": "检索入库",
        "execution_status": "prepared_not_executed",
        "requires_user_authorization_for_real_search": True,
        "allowed_real_executor": "检索入库",
        "allowed_server_entry_if_authorized": "ss" + "h ubuntu@beijing",
        "forbidden_for_referencefootnote": [
            "CNKI/WoS direct search",
            "Zotero save",
            "PDF retrieval",
            "RAG ingestion",
            "localhost" + ":22 probe",
            "openclaw" + "-cnki-takeover operation"
        ],
        "handoff": handoff,
        "expected_completion_schema": {
            "completion_id": "string",
            "handoff_id": handoff.get("handoff_id", ""),
            "batch_id": handoff.get("batch_id", ""),
            "status": "completed|partial|failed",
            "results": ["request_id", "claim_id", "status", "sources_found", "kb_routing", "pdf_status", "import_status", "zotero_id", "ref_metadata"],
        },
        "next_referencefootnote_step": "apply-intake-completion.py, then build-post-ingestion-rag-call.py",
        "errors": errors,
    }
    out_dir = task / "state" / "search-intake-calls"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / f"{args.batch_id}.json"
    prompt_out = out_dir / f"{args.batch_id}.prompt.md"
    write_json(json_out, package)
    prompt_out.write_text(render_prompt(package), encoding="utf-8")
    print_json(result("failed" if errors else "passed", output=str(json_out), prompt=str(prompt_out), errors=errors))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
