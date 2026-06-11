#!/usr/bin/env python3
"""Run offline startup and boundary checks."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ROOT, ensure_task, print_json, result, update_flow_status, write_json
from wenheng_native import add_wenheng_args, verify_wenheng_native

REQUIRED = ["SKILL.md", "docs", "references", "scripts", "templates", "config", "agents", "server-assets", "tests/fixtures", "VERSION"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", type=Path, default=ROOT)
    parser.add_argument("--existing-rag-library", action="store_true", help="user declares a usable RAG library already exists")
    add_wenheng_args(parser)
    args = parser.parse_args()
    wenheng_binding = verify_wenheng_native(args, skill_id="reference_footnote", task_type="reference_footnote", writing=True)
    errors = [f"missing required path: {rel}" for rel in REQUIRED if not (ROOT / rel).exists()]
    blocked = {
        "cnki_wos_zotero_pdf_rag": True,
        "openclaw_cnki_takeover": True,
        "localhost_22_probe": True,
        "server_deploy": True,
        "formal_article_task": True,
    }
    data = result(
        "failed" if errors else "passed",
        errors=errors,
        boundaries_blocked=blocked,
        rag_library_status="user_declared_existing" if args.existing_rag_library else "not_declared",
        wenheng_native_binding=wenheng_binding,
    )
    task = ensure_task(args.task_dir)
    write_json(task / "state" / "status.json", data)
    update_flow_status(task, "S00", status=data["status"], blocked=bool(errors), note="startup boundary check")
    print_json(data)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
