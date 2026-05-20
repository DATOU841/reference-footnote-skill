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
SUPPORT_STRENGTHS = {
    "strong_support",
    "partial_support",
    "analogy_only",
    "background_only",
    "conflict",
    "no_support",
    "no_support_found",
}
GROUNDING_STATUSES = {
    "full_markdown_grounding",
    "page_mapped_grounding",
    "chunk_only_grounding",
    "pdf_fallback_required",
    "unresolved_grounding",
    "not_resolved",
}
LAYOUT_RISK_TRIGGERS = {
    "ocr_uncertain",
    "vertical_text",
    "table_complex",
    "figure_embedded",
    "formula_inline",
    "footnote_in_source",
    "page_map_conflict",
    "markdown_page_map_missing",
}
RISK_FLAGS = {
    "page_missing", "ocr_uncertain", "secondhand_citation", "concept_approximate",
    "temporal_mismatch", "discipline_cross", "translation_gap", "pdf_rag_conflict",
    "wrong_insertion_position", "reference_only_in_footnote", "low_material",
    "vertical_text", "table_complex", "figure_embedded", "formula_inline",
    "footnote_in_source", "page_map_conflict", "markdown_not_available",
    "markdown_page_map_missing", "chunk_only_grounding", "ownership_unverified",
    "direct_experiment_missing"
}
NOTE_TYPES = {"footnote", "endnote", "reference_only"}
ANNOTATION_PURPOSES = {
    "evidence", "clarification", "supplement", "source_anchor", "counter_view",
    "background", "reference_only"
}
AUTHENTICITY_STATUSES = {"verified", "human_review", "failed", "not_checked"}
WRITING_POOL_DECISIONS = {"keep", "revise_note", "move_note", "drop_note", "return_paragraph_for_rewrite"}
FINAL_DECISIONS = {
    "pending",
    "inserted",
    "no_note_needed",
    "deleted_by_cleanup",
    "downgraded_by_cleanup",
    "needs_gap_handoff",
    "needs_human_review",
    "blocked_rewrite_required",
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
    if strength == "analogy_only":
        return "类比旁证"
    return "浅要参考"


def normalize_support_strength(strength: str | None) -> str:
    if strength == "no_support_found":
        return "no_support"
    if strength in SUPPORT_STRENGTHS:
        return strength or "no_support"
    return "no_support"


def resolve_grounding_status(
    *,
    chunk_text: str | None = None,
    markdown_path: str | None = None,
    parsed_text_path: str | None = None,
    page_map: object | None = None,
    risk_flags: list[str] | None = None,
) -> str:
    """Resolve grounding status from available parsed artifacts.

    RAG chunk text proves that ingestion parsed the source enough for retrieval.
    Markdown/parsed text is the default context-verification layer; PDF is only
    a fallback when page maps or layout-sensitive evidence require it.
    """
    risks = set(risk_flags or [])
    if not chunk_text:
        return "unresolved_grounding"
    if risks & LAYOUT_RISK_TRIGGERS:
        return "pdf_fallback_required"
    if markdown_path or parsed_text_path:
        return "full_markdown_grounding"
    if page_map:
        if isinstance(page_map, dict) and page_map.get("conflict"):
            return "pdf_fallback_required"
        return "page_mapped_grounding"
    return "chunk_only_grounding"


def material_flag(chars: int | None) -> str:
    chars = int(chars or 0)
    if chars < 50:
        return "very_low"
    if chars < 150:
        return "below_average"
    return "normal"


def pool_material_status(avg_chars: float) -> str:
    return "sufficient" if avg_chars >= 200 else "insufficient"


def annotation_purpose_for(entry: dict, candidate: dict | None = None) -> str:
    candidate = candidate or {}
    strength = candidate.get("support_assessment", {}).get("strength", entry.get("evidence_status"))
    if strength == "conflict":
        return "counter_view"
    if entry.get("claim_type") == "definition":
        return "clarification"
    if entry.get("need_level") == "critical":
        return "source_anchor"
    if entry.get("evidence_status") == "partial_support":
        return "supplement"
    return "evidence"


def necessity_score(entry: dict, candidate: dict | None = None, material: dict | None = None) -> float:
    candidate = candidate or {}
    material = material or {}
    score = 0.0
    score += {"critical": 45, "important": 32, "recommended": 22, "not_needed": 0}.get(entry.get("need_level"), 12)
    score += {"strong_support": 30, "partial_support": 15, "background_only": 5, "conflict": 8}.get(entry.get("evidence_status"), 0)
    confidence = candidate.get("support_assessment", {}).get("confidence", 0) or 0
    score += min(float(confidence), 1.0) * 10
    risks = candidate.get("risks", entry.get("risks", [])) or []
    score -= min(len(risks) * 4, 16)
    flag = material.get("material_flag")
    if flag == "very_low":
        score -= 14
    elif flag == "below_average":
        score -= 6
    return round(max(score, 0.0), 2)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_flow_status(task_dir: Path, stage: str, *, status: str = "completed", blocked: bool = False, note: str | None = None) -> None:
    state_path = task_dir / "state" / "referencefootnote-flow-status.json"
    existing = read_json(state_path) if state_path.exists() else {
        "version": VERSION,
        "current_stage": None,
        "completed_stages": [],
        "blocked_at": None,
        "block_reason": None,
        "pending_actions": [],
    }
    completed = list(existing.get("completed_stages", []))
    if not blocked and stage not in completed:
        completed.append(stage)
    existing.update({
        "version": VERSION,
        "current_stage": stage,
        "completed_stages": completed,
        "blocked_at": stage if blocked else None,
        "block_reason": note if blocked else None,
        "last_updated": now(),
        "last_status": status,
    })
    if note and not blocked:
        existing["last_note"] = note
    write_json(state_path, existing)


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
