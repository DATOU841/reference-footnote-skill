#!/usr/bin/env python3
"""Build a complete Markdown full text with note markers and references."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, read_json, result, update_flow_status, write_json


def ref_line(ref: dict, idx: int) -> str:
    authors = ", ".join(ref.get("authors", ["佚名"]))
    title = ref.get("title", "未题名文献")
    source = ref.get("source", "")
    year = ref.get("year", "")
    pages = ref.get("pages", "")
    return f"[{idx}] {authors}. {title}[J]. {source}, {year}: {pages}."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    article_path = task / "state" / "article-structure.json"
    plan_path = task / "state" / "cleaned-insertion-plan.json"
    if not plan_path.exists():
        plan_path = task / "state" / "insertion-plan.json"
    if not article_path.exists() or not plan_path.exists():
        print_json(result("failed", errors=["article-structure.json or insertion plan missing"]))
        return 1
    article = read_json(article_path)
    plan = read_json(plan_path)
    marker_by_sentence = {}
    notes = []
    for idx, ins in enumerate(plan.get("insertions", []), start=1):
        loc = ins.get("target_location", {})
        marker_by_sentence[loc.get("sentence_id")] = f"〔注{idx}〕"
        notes.append((idx, ins.get("footnote_content", {}).get("text") or ins.get("gbt7714_footnote") or "注释内容待补。"))
    lines = [f"# {article.get('title', 'Untitled')}", ""]
    sections = {s.get("section_id"): s for s in article.get("sections", [])}
    last_section = None
    for para in article.get("paragraphs", []):
        sec = sections.get(para.get("section_id"))
        if sec and sec.get("section_id") != last_section and sec.get("level", 2) > 1:
            lines.extend([f"{'#' * sec.get('level', 2)} {sec.get('title')}", ""])
            last_section = sec.get("section_id")
        text = para.get("text", "")
        for sent in para.get("sentences", []):
            marker = marker_by_sentence.get(sent.get("sentence_id"))
            if marker and sent.get("text") in text:
                text = text.replace(sent.get("text"), sent.get("text") + marker, 1)
        lines.extend([text, ""])
    if notes:
        lines.extend(["# 注释", ""])
        for idx, note in notes:
            lines.extend([f"〔注{idx}〕{note}", ""])
    refs = plan.get("reference_list", {}).get("new_references", [])
    if refs:
        lines.extend(["# 参考文献", ""])
        for idx, ref in enumerate(refs, start=1):
            lines.append(ref_line(ref, idx))
    markdown = "\n".join(lines).rstrip() + "\n"
    out_md = task / "state" / "full-text-with-notes.md"
    out_md.write_text(markdown, encoding="utf-8")
    write_json(task / "state" / "full-text-insertion-result.json", {
        "status": "passed",
        "markdown": str(out_md),
        "docx": None,
        "notes": len(notes),
        "references": len(refs),
    })
    update_flow_status(task, "S100", note=f"full text notes={len(notes)} refs={len(refs)}")
    print_json(result("passed", markdown=str(out_md), notes=len(notes), references=len(refs)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
