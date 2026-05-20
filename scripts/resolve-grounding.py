#!/usr/bin/env python3
"""Resolve RAG evidence grounding against intake handoff artifacts.

This is an offline resolver. It does not read remote PDFs or call RAG. It links
RAG candidates to any available Markdown/parsed text/page-map metadata and marks
PDF checks only as fallback work.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import (
    LAYOUT_RISK_TRIGGERS,
    ensure_task,
    print_json,
    read_json,
    resolve_grounding_status,
    result,
    write_json,
)


def maybe_read(path: Path) -> dict:
    return read_json(path) if path.exists() else {}


def iter_interpretations(task: Path) -> list[dict]:
    items: list[dict] = []
    for path in sorted((task / "state" / "evidence-interpretations").glob("*.json")):
        batch = read_json(path)
        for interp in batch.get("interpretations", []):
            for idx, cand in enumerate(interp.get("candidates", []), start=1):
                items.append({
                    "batch_id": batch.get("batch_id", path.stem),
                    "claim_id": interp.get("claim_id"),
                    "candidate_index": idx,
                    "candidate_id": cand.get("candidate_id") or f"{interp.get('claim_id')}-cand-{idx:02d}",
                    "candidate": cand,
                })
    return items


def collect_intake_records(task: Path) -> dict[str, dict]:
    records: dict[str, dict] = {}
    for name in ["intake-status.json", "intake-status-round2.json"]:
        data = maybe_read(task / "state" / name)
        for row in data.get("results", []):
            keys = [
                row.get("item_key"),
                row.get("zotero_id"),
                row.get("ref_id"),
                row.get("source_file"),
                row.get("pdf_path"),
                row.get("title"),
            ]
            for key in keys:
                if key:
                    records[str(key)] = row
    return records


def collect_artifacts(task: Path, handoff_dir: Path | None) -> dict[str, dict]:
    artifacts: dict[str, dict] = {}
    candidates = [
        task / "state" / "artifact-resolver-map.json",
        task / "artifact-resolver-map.json",
    ]
    if handoff_dir:
        candidates.extend([
            handoff_dir / "artifact-resolver-map.json",
            handoff_dir / "025-rag-import" / "artifact-resolver-map.json",
        ])
    for path in candidates:
        if not path.exists():
            continue
        data = read_json(path)
        rows = data.get("items") or data.get("sources") or data.get("artifacts") or []
        if isinstance(data, dict) and not rows:
            rows = [v for v in data.values() if isinstance(v, dict)]
        for row in rows:
            keys = [
                row.get("item_key"),
                row.get("file_id"),
                row.get("source_file"),
                row.get("pdf_path"),
                row.get("title"),
            ]
            for key in keys:
                if key:
                    artifacts[str(key)] = row
    return artifacts


def source_keys(cand: dict) -> list[str]:
    ref = cand.get("reference", {}) or {}
    details = cand.get("match_details", {}) or {}
    keys = [
        cand.get("item_key"),
        cand.get("zotero_id"),
        cand.get("file_id"),
        cand.get("source_file"),
        cand.get("pdf_path"),
        cand.get("title"),
        ref.get("item_key"),
        ref.get("ref_id"),
        ref.get("title"),
        details.get("source_file"),
        details.get("file_id"),
    ]
    source_file = cand.get("source_file") or details.get("source_file")
    if source_file and "-" in str(source_file):
        keys.append(str(source_file).split("-", 1)[0])
    return [str(k) for k in keys if k]


def first_value(*values: object) -> object | None:
    for value in values:
        if value not in (None, "", []):
            return value
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--handoff-dir", type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    intake_records = collect_intake_records(task)
    artifact_records = collect_artifacts(task, args.handoff_dir)
    resolved = []
    summary = {k: 0 for k in [
        "full_markdown_grounding",
        "page_mapped_grounding",
        "chunk_only_grounding",
        "pdf_fallback_required",
        "unresolved_grounding",
    ]}
    for item in iter_interpretations(task):
        cand = item["candidate"]
        match = cand.get("match_details", {}) or {}
        artifact = {}
        intake = {}
        for key in source_keys(cand):
            artifact = artifact_records.get(key, artifact)
            intake = intake_records.get(key, intake)
            if artifact or intake:
                break
        risks = list(dict.fromkeys(cand.get("risks", []) or cand.get("support_assessment", {}).get("risks", []) or []))
        page_map = first_value(cand.get("page_map"), match.get("page_map"), artifact.get("page_map"), intake.get("page_map"))
        if isinstance(page_map, dict) and page_map.get("conflict") and "page_map_conflict" not in risks:
            risks.append("page_map_conflict")
        chunk_text = first_value(cand.get("chunk_text"), cand.get("snippet"), match.get("snippet"), cand.get("text"))
        markdown_path = first_value(cand.get("markdown_path"), match.get("markdown_path"), artifact.get("markdown_path"), intake.get("markdown_path"))
        parsed_text_path = first_value(cand.get("parsed_text_path"), match.get("parsed_text_path"), artifact.get("parsed_text_path"), intake.get("parsed_text_path"))
        status = resolve_grounding_status(
            chunk_text=str(chunk_text) if chunk_text else None,
            markdown_path=str(markdown_path) if markdown_path else None,
            parsed_text_path=str(parsed_text_path) if parsed_text_path else None,
            page_map=page_map,
            risk_flags=risks,
        )
        if status == "chunk_only_grounding" and "chunk_only_grounding" not in risks:
            risks.append("chunk_only_grounding")
        if status == "pdf_fallback_required":
            if any(r in LAYOUT_RISK_TRIGGERS for r in risks):
                fallback_reason = "layout_or_page_mapping_risk"
            else:
                fallback_reason = "pdf_visual_check_required"
        elif status == "unresolved_grounding":
            fallback_reason = "source_unresolved"
        else:
            fallback_reason = None
        summary[status] += 1
        resolved.append({
            "batch_id": item["batch_id"],
            "claim_id": item["claim_id"],
            "candidate_id": item["candidate_id"],
            "grounding_status": status,
            "resolved_source": {
                "chunk_text": chunk_text,
                "source_file": first_value(cand.get("source_file"), match.get("source_file"), artifact.get("source_file"), intake.get("source_file")),
                "item_key": first_value(cand.get("item_key"), artifact.get("item_key"), intake.get("item_key"), intake.get("zotero_id")),
                "file_id": first_value(cand.get("file_id"), match.get("file_id"), artifact.get("file_id")),
                "kb_id": first_value(cand.get("kb_id"), match.get("kb_id"), artifact.get("kb_id"), intake.get("kb_id")),
                "markdown_path": markdown_path,
                "parsed_text_path": parsed_text_path,
                "page_map": page_map,
                "pdf_path": first_value(cand.get("pdf_path"), artifact.get("pdf_path"), intake.get("pdf_path")),
            },
            "risk_flags": risks,
            "fallback_reason": fallback_reason,
        })
    out_data = {"resolved_items": resolved, "summary": summary}
    out = task / "state" / "grounding-resolution.json"
    write_json(out, out_data)
    print_json(result("passed", output=str(out), resolved=len(resolved), summary=summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
