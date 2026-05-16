#!/usr/bin/env python3
"""Import a written article into an offline article structure."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import ensure_task, print_json, result, split_sentences, write_json


def parse_markdown(text: str) -> dict:
    title = "Untitled"
    sections = []
    paragraphs = []
    current_section = None
    pnum = 1
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            name = line.lstrip("#").strip()
            if level == 1:
                title = name
            sid = f"sec-{len(sections)+1:02d}"
            current_section = sid
            sections.append({"section_id": sid, "title": name, "level": level, "paragraphs": []})
            continue
        pid = f"p-{pnum:03d}"
        sentences = [{"sentence_id": f"{pid}-s-{i+1}", "text": sent} for i, sent in enumerate(split_sentences(line))]
        paragraphs.append({"paragraph_id": pid, "section_id": current_section or "sec-00", "text": line, "sentences": sentences})
        if sections:
            sections[-1]["paragraphs"].append(pid)
        pnum += 1
    return {
        "article_id": "article-fixture",
        "title": title,
        "sections": sections,
        "paragraphs": paragraphs,
        "existing_references": [],
        "metadata": {"language": "zh-CN", "discipline": "law", "total_paragraphs": len(paragraphs)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--file", required=True, type=Path)
    args = parser.parse_args()
    if not args.file.exists():
        print_json(result("failed", errors=[f"article file missing: {args.file}"]))
        return 1
    task = ensure_task(args.task_dir)
    structure = parse_markdown(args.file.read_text(encoding="utf-8"))
    if not structure["paragraphs"]:
        print_json(result("failed", errors=["article has no paragraphs"]))
        return 1
    out = task / "state" / "article-structure.json"
    write_json(out, structure)
    print_json(result("passed", output=str(out), paragraphs=len(structure["paragraphs"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
