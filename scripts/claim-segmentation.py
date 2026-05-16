#!/usr/bin/env python3
"""Segment article sentences into claims."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import classify_claim, ensure_task, print_json, read_json, result, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    article_path = task / "state" / "article-structure.json"
    if not article_path.exists():
        print_json(result("failed", errors=["article-structure.json missing"]))
        return 1
    article = read_json(article_path)
    claims = []
    idx = 1
    for para in article["paragraphs"]:
        section = next((s for s in article["sections"] if s["section_id"] == para["section_id"]), {})
        for sent in para["sentences"]:
            claim_type = classify_claim(sent["text"])
            claims.append({
                "claim_id": f"c-{idx:03d}",
                "source_sentence_id": sent["sentence_id"],
                "paragraph_id": para["paragraph_id"],
                "section_title": section.get("title", ""),
                "text": sent["text"],
                "claim_type": claim_type,
                "no_force_insert": claim_type in {"author_opinion", "common_knowledge", "transitional"},
            })
            idx += 1
    out_data = {"article_id": article["article_id"], "claims": claims}
    out = task / "state" / "claim-segments.json"
    write_json(out, out_data)
    print_json(result("passed", output=str(out), claims=len(claims)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
