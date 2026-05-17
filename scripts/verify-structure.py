#!/usr/bin/env python3
"""Verify ReferenceFootnote skill structure."""

from __future__ import annotations

import argparse
from reflib import ROOT, print_json

REQUIRED = [
    "SKILL.md", "README.md", "VERSION", "CHANGELOG.md", "RELEASE.md", ".gitignore",
    "docs/architecture.md", "docs/state-machine.md", "docs/rag-protocol.md",
    "docs/handoff-protocol.md", "docs/evidence-classification.md", "docs/claim-taxonomy.md",
    "docs/quality-gates.md", "docs/boundary-rules.md", "docs/glossary.md",
    "docs/collaboration-flow.md",
    "references/scholar-polish-protocol.md", "references/search-intake-interface.md",
    "references/writing-skill-interface.md", "references/rag-platform-interface.md",
    "config/skill.yaml", "config/boundaries.yaml",
    "config/quality-thresholds.yaml", "config/claim-types.yaml", "config/citation-styles.yaml",
    "config/rag-protocol.yaml", "agents/claim-segmenter.md", "agents/citation-diagnostician.md",
    "agents/rag-interpreter.md", "agents/footnote-planner.md", "agents/quality-auditor.md",
    "agents/coordinator.md", "server-assets/deploy-staging.sh", "server-assets/deploy-production.sh",
    "server-assets/server-config.template.yaml", "templates/article-structure.template.json",
    "templates/claim-segments.template.json", "templates/citation-needs.template.json",
    "templates/rag-lookup-request.template.json", "templates/rag-lookup-response.template.json",
    "templates/evidence-map.template.json", "templates/search-intake-request.template.json",
    "templates/intake-completion.template.json", "templates/insertion-plan.template.json",
    "templates/quality-report.template.json", "scripts/build-search-intake-call.py",
    "scripts/build-post-ingestion-rag-call.py", "tests/fixtures/README.md",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="reference-footnote")
    args = parser.parse_args()
    errors = [f"missing required path: {rel}" for rel in REQUIRED if not (ROOT / rel).exists()]
    skill = ROOT / "SKILL.md"
    lines = len(skill.read_text(encoding="utf-8").splitlines()) if skill.exists() else 0
    print_json({"ok": not errors, "errors": errors, "target": args.target, "skill_lines": lines})
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
