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


def search_dimensions_for_text(text: str) -> dict:
    terms = [w for w in ["平台", "规则", "比例原则", "产权", "自动化审核", "申诉", "透明度"] if w in text]
    english = {
        "平台": "platform",
        "规则": "rules",
        "比例原则": "proportionality principle",
        "产权": "property rights",
        "自动化审核": "automated review",
        "申诉": "appeal mechanism",
        "透明度": "transparency",
    }
    return {
        "semantic": {"query": text, "weight": 0.4},
        "keyword": {"terms": terms or [text[:12]], "weight": 0.2},
        "keyword_en": {"terms": [english[t] for t in terms if t in english], "weight": 0.1},
        "concept": {"concepts": terms, "ontology_hints": [], "weight": 0.2},
        "author": {"names": [], "weight": 0.1},
        "theory": {"terms": [t for t in terms if t in {"比例原则", "产权"}], "weight": 0.1},
        "citation_network": {"known_refs": [], "weight": 0.1},
    }


def infer_evidence_type(claim_type: str, ref: dict | None = None) -> str:
    ref = ref or {}
    if claim_type in {"theoretical_claim", "academic_judgment", "definition"}:
        return "后设归纳"
    if claim_type in {"factual_claim", "data_judgment", "historical_narrative"}:
        return "材料依据"
    if ref.get("source_type") == "primary_source":
        return "一手材料"
    return "文本证据"


def infer_source_role(claim_type: str, citation_type: str | None = None) -> str:
    if citation_type == "authority" or claim_type == "theoretical_claim":
        return "理论锚点"
    if claim_type == "definition":
        return "概念界定"
    if claim_type in {"academic_judgment", "historical_narrative"}:
        return "学术史定位"
    if claim_type in {"factual_claim", "data_judgment"}:
        return "材料依据"
    if claim_type == "policy_judgment":
        return "关键争议"
    return "旁证补充"


def consumption_depth_for_strength(strength: str, risks: list[str] | None = None) -> str:
    risks = risks or []
    if strength == "strong_support" and not risks:
        return "深度消费"
    return "浅要参考"


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
