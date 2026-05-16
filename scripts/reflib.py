#!/usr/bin/env python3
"""Shared helpers for ReferenceFootnote offline scripts."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").exists() else ""

PROTECTED_TYPES = {"author_opinion", "common_knowledge", "transitional"}
SUPPORT_STRENGTHS = {"strong_support", "partial_support", "background_only", "conflict", "no_support"}
RISK_FLAGS = {
    "page_missing", "ocr_uncertain", "secondhand_citation", "concept_approximate",
    "temporal_mismatch", "discipline_cross", "translation_gap"
}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def print_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def result(status: str, **extra: object) -> dict:
    data = {"status": status, "created_at": now(), "version": VERSION}
    data.update(extra)
    return data


def ensure_task(task_dir: Path) -> Path:
    task_dir.mkdir(parents=True, exist_ok=True)
    for rel in ["state", "state/rag-requests", "state/evidence-interpretations", "state/search-intake-requests", "delivery"]:
        (task_dir / rel).mkdir(parents=True, exist_ok=True)
    return task_dir


def split_sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[。！？；])", text)
    return [p.strip() for p in pieces if p.strip()]


def classify_claim(text: str) -> str:
    if "笔者认为" in text or "本文认为" in text:
        return "author_opinion"
    if "下文" in text or "本文将" in text:
        return "transitional"
    if "学界普遍认为" in text:
        return "academic_judgment"
    if "比例原则" in text or "产权" in text:
        return "theoretical_claim"
    if "研究显示" in text or "近年" in text or "若干" in text:
        return "factual_claim"
    if "应当" in text or "义务" in text or "救济" in text:
        return "policy_judgment"
    if "已经成为" in text:
        return "common_knowledge"
    return "logical_inference"


def diagnose_need(claim_type: str, text: str) -> tuple[str, str]:
    if claim_type in PROTECTED_TYPES or claim_type == "common_knowledge":
        return "not_needed", "none"
    if "学界普遍认为" in text or claim_type in {"theoretical_claim", "policy_judgment"}:
        return "critical", "secondary_source"
    if "研究显示" in text or claim_type == "factual_claim":
        return "important", "empirical"
    return "recommended", "secondary_source"


def run_command(args: list[str], cwd: Path = ROOT) -> tuple[int, str, str]:
    proc = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout, proc.stderr


def copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
