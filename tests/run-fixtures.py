#!/usr/bin/env python3
"""Run ReferenceFootnote offline fixtures."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTICLE = ROOT / "tests" / "fixtures" / "articles" / "sample-law-article.md"
RAG = ROOT / "tests" / "fixtures" / "mocks" / "rag-service-mock.json"
COMPLETION = ROOT / "tests" / "fixtures" / "mocks" / "intake-completion.json"
FULL_COMPLETION = ROOT / "tests" / "fixtures" / "fixture-intake-completion-full.json"
POST_INGESTION_RAG = ROOT / "tests" / "fixtures" / "mocks" / "post-ingestion-rag-response.json"
AUTHENTICITY = ROOT / "tests" / "fixtures" / "mocks" / "authenticity-verification-result.json"
INITIAL_COMPLETION = ROOT / "tests" / "fixtures" / "mocks" / "intake-completion-initial-library.json"
INITIAL_COMPLETION_SMALL = ROOT / "tests" / "fixtures" / "mocks" / "intake-completion-initial-library-small.json"
INITIAL_COMPLETION_LOW = ROOT / "tests" / "fixtures" / "mocks" / "intake-completion-initial-library-low-material.json"
INITIAL_COMPLETION_NARROW = ROOT / "tests" / "fixtures" / "mocks" / "intake-completion-initial-library-narrow.json"
GAP_ROUND2_COMPLETION = ROOT / "tests" / "fixtures" / "mocks" / "intake-completion-gap-round2.json"
RAG_AFTER_LIBRARY = ROOT / "tests" / "fixtures" / "mocks" / "rag-response-after-library.json"


def run(args: list[str]) -> tuple[int, dict]:
    proc = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {"stdout": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, data


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def base_flow(task: Path, *, include_rag: bool = True, allow_fail: bool = True) -> None:
    steps = [
        ["python3", "scripts/startup.py", "--task-dir", str(task)],
        ["python3", "scripts/article-intake.py", "--task-dir", str(task), "--file", str(ARTICLE)],
        ["python3", "scripts/claim-segmentation.py", "--task-dir", str(task)],
        ["python3", "scripts/citation-need-diagnosis.py", "--task-dir", str(task)],
        ["python3", "scripts/build-rag-request.py", "--task-dir", str(task), "--batch-id", "batch-01", "--allow-pre-ingestion"],
    ]
    for step in steps:
        code, data = run(step)
        assert code == 0, data
    if include_rag:
        req = task / "state" / "rag-requests" / "batch-01.json"
        code, data = run(["python3", "scripts/validate-rag-response.py", "--task-dir", str(task), "--request", str(req), "--response", str(RAG)])
        assert code == 0, data
    code, data = run(["python3", "scripts/build-evidence-map.py", "--task-dir", str(task)])
    assert code == 0, data
    code, data = run(["python3", "scripts/build-search-handoff.py", "--task-dir", str(task), "--batch-id", "batch-01", "--macro-round", "round1"])
    assert code == 0, data
    code, data = run(["python3", "scripts/apply-intake-completion.py", "--task-dir", str(task), "--completion", str(COMPLETION)])
    assert code == 0, data
    code, data = run(["python3", "scripts/build-footnote-candidate-pool.py", "--task-dir", str(task)])
    assert code == 0, data
    code, data = run(["python3", "scripts/prune-footnotes.py", "--task-dir", str(task)])
    assert code == 0, data
    code, data = run(["python3", "scripts/prune-references.py", "--task-dir", str(task)])
    assert code == 0, data
    code, data = run(["python3", "scripts/plan-footnotes.py", "--task-dir", str(task)])
    assert code == 0, data
    code, data = run(["python3", "scripts/build-authenticity-verification-request.py", "--task-dir", str(task)])
    assert code == 0, data
    request = read(task / "state" / "authenticity-verification-request.json")
    auth_results = []
    for idx, item in enumerate(request.get("items", []), start=1):
        auth_results.append({
            "insertion_id": item["insertion_id"],
            "authenticity_status": "human_review" if idx == 2 else "verified",
            "pdf_check": {"reference_exists": True, "metadata_matches": True, "page": 36 if idx != 2 else None, "contains_cited_content": True if idx != 2 else "uncertain"},
            "rag_pdf_consistency": "consistent" if idx != 2 else "uncertain",
            "claim_fit": "fits" if idx != 2 else "partial",
            "insertion_position_fit": "fits",
            "risks": [] if idx != 2 else ["page_missing", "ocr_uncertain"],
            "resolution_required": None if idx != 2 else "manual_page_check",
        })
    auth_path = task / "state" / "fixture-authenticity-result.json"
    write(auth_path, {"status": "completed", "batch_id": "authenticity-01", "results": auth_results})
    code, data = run(["python3", "scripts/apply-authenticity-verification-result.py", "--task-dir", str(task), "--verification", str(auth_path)])
    assert code == 0, data
    code, data = run(["python3", "scripts/validate-note-reference-consistency.py", "--task-dir", str(task), "--allow-fail"])
    assert code == 0, data
    cmd = ["python3", "scripts/validate-citation-plan.py", "--task-dir", str(task)]
    if allow_fail:
        cmd.append("--allow-fail")
    code, data = run(cmd)
    assert code == 0, data
    code, data = run(["python3", "scripts/build-delivery.py", "--task-dir", str(task)])
    assert code == 0, data


def base_flow_retrieval_first(task: Path, *, allow_fail: bool = True) -> None:
    steps = [
        ["python3", "scripts/startup.py", "--task-dir", str(task)],
        ["python3", "scripts/article-intake.py", "--task-dir", str(task), "--file", str(ARTICLE)],
        ["python3", "scripts/claim-segmentation.py", "--task-dir", str(task)],
        ["python3", "scripts/citation-need-diagnosis.py", "--task-dir", str(task)],
        ["python3", "scripts/build-search-blueprint.py", "--task-dir", str(task)],
        ["python3", "scripts/build-initial-search-handoff.py", "--task-dir", str(task)],
        ["python3", "scripts/build-search-intake-call.py", "--task-dir", str(task), "--batch-id", "initial-library"],
        ["python3", "scripts/apply-intake-completion.py", "--task-dir", str(task), "--completion", str(INITIAL_COMPLETION)],
        ["python3", "scripts/validate-intake-quality.py", "--task-dir", str(task)],
        ["python3", "scripts/build-rag-request.py", "--task-dir", str(task), "--batch-id", "batch-01"],
    ]
    for step in steps:
        code, data = run(step)
        assert code == 0, data
    req = task / "state" / "rag-requests" / "batch-01.json"
    code, data = run(["python3", "scripts/validate-rag-response.py", "--task-dir", str(task), "--request", str(req), "--response", str(RAG_AFTER_LIBRARY)])
    assert code == 0, data
    for step in [
        ["python3", "scripts/build-evidence-map.py", "--task-dir", str(task)],
        ["python3", "scripts/build-search-handoff.py", "--task-dir", str(task)],
        ["python3", "scripts/build-search-intake-call.py", "--task-dir", str(task), "--batch-id", "gap-round2"],
        ["python3", "scripts/build-footnote-candidate-pool.py", "--task-dir", str(task)],
        ["python3", "scripts/prune-footnotes.py", "--task-dir", str(task)],
        ["python3", "scripts/prune-references.py", "--task-dir", str(task)],
        ["python3", "scripts/plan-footnotes.py", "--task-dir", str(task)],
        ["python3", "scripts/build-authenticity-verification-request.py", "--task-dir", str(task)],
    ]:
        code, data = run(step)
        assert code == 0, data
    request = read(task / "state" / "authenticity-verification-request.json")
    auth_results = [{
        "insertion_id": item["insertion_id"],
        "authenticity_status": "verified",
        "pdf_check": {"reference_exists": True, "metadata_matches": True, "page": 5, "contains_cited_content": True},
        "rag_pdf_consistency": "consistent",
        "claim_fit": "fits",
        "insertion_position_fit": "fits",
        "risks": [],
        "resolution_required": None,
    } for item in request.get("items", [])]
    auth_path = task / "state" / "fixture-authenticity-result.json"
    write(auth_path, {"status": "completed", "batch_id": "authenticity-01", "results": auth_results})
    for step in [
        ["python3", "scripts/apply-authenticity-verification-result.py", "--task-dir", str(task), "--verification", str(auth_path)],
        ["python3", "scripts/validate-note-reference-consistency.py", "--task-dir", str(task), "--allow-fail"],
    ]:
        code, data = run(step)
        assert code == 0, data
    cmd = ["python3", "scripts/validate-citation-plan.py", "--task-dir", str(task)]
    if allow_fail:
        cmd.append("--allow-fail")
    code, data = run(cmd)
    assert code == 0, data
    code, data = run(["python3", "scripts/build-delivery.py", "--task-dir", str(task)])
    assert code == 0, data


def prepare_blueprint(task: Path) -> None:
    for step in [
        ["python3", "scripts/article-intake.py", "--task-dir", str(task), "--file", str(ARTICLE)],
        ["python3", "scripts/claim-segmentation.py", "--task-dir", str(task)],
        ["python3", "scripts/citation-need-diagnosis.py", "--task-dir", str(task)],
        ["python3", "scripts/build-search-blueprint.py", "--task-dir", str(task)],
    ]:
        code, data = run(step)
        assert code == 0, data


def prepare_initial_call(task: Path) -> None:
    prepare_blueprint(task)
    code, data = run(["python3", "scripts/build-initial-search-handoff.py", "--task-dir", str(task)])
    assert code == 0, data
    code, data = run(["python3", "scripts/build-search-intake-call.py", "--task-dir", str(task), "--batch-id", "initial-library"])
    assert code == 0, data


def fixture_01(base: Path) -> None:
    task = base / "article-intake-basic"
    code, data = run(["python3", "scripts/article-intake.py", "--task-dir", str(task), "--file", str(ARTICLE)])
    assert code == 0, data
    article = read(task / "state" / "article-structure.json")
    assert article["paragraphs"] and article["sections"]


def fixture_02(base: Path) -> None:
    task = base / "claim-segmentation-law"
    fixture_01_task(task)
    code, data = run(["python3", "scripts/claim-segmentation.py", "--task-dir", str(task)])
    assert code == 0, data
    claims = read(task / "state" / "claim-segments.json")["claims"]
    assert any(c["claim_type"] == "author_opinion" for c in claims)


def fixture_01_task(task: Path) -> None:
    code, data = run(["python3", "scripts/article-intake.py", "--task-dir", str(task), "--file", str(ARTICLE)])
    assert code == 0, data


def fixture_03(base: Path) -> None:
    task = base / "rag-strong-support"
    base_flow(task)
    evidence = read(task / "state" / "evidence-map.json")
    assert evidence["coverage_summary"]["strong_support"] >= 1


def fixture_04(base: Path) -> None:
    task = base / "rag-partial-support"
    base_flow(task)
    evidence = read(task / "state" / "evidence-map.json")
    assert evidence["coverage_summary"]["partial_support"] >= 1


def fixture_05(base: Path) -> None:
    task = base / "rag-no-support-handoff"
    base_flow(task)
    handoff = read(task / "state" / "search-intake-requests" / "batch-01.json")
    assert handoff["target_skill"] == "检索入库"
    assert handoff["requests"]


def fixture_06(base: Path) -> None:
    task = base / "post-ingestion-relookup"
    base_flow(task)
    intake = read(task / "state" / "intake-status.json")
    assert intake["status"] == "completed"


def fixture_07(base: Path) -> None:
    task = base / "page-missing-risk"
    base_flow(task)
    evidence = read(task / "state" / "evidence-map.json")
    assert any("page_missing" in e["risks"] for e in evidence["claim_evidence"])


def fixture_08(base: Path) -> None:
    task = base / "evidence-conflict"
    base_flow(task)
    evidence = read(task / "state" / "evidence-map.json")
    assert evidence["coverage_summary"]["conflict"] >= 1


def fixture_09(base: Path) -> None:
    task = base / "no-force-insert"
    base_flow(task)
    plan = read(task / "state" / "insertion-plan.json")
    assert any("author_opinion" in item["reason"] for item in plan["no_insert_zones"])


def fixture_10(base: Path) -> None:
    task = base / "footnote-plan-complete"
    base_flow(task)
    plan = read(task / "state" / "insertion-plan.json")
    assert plan["insertions"] and plan["reference_list"]["new_references"]


def fixture_11(base: Path) -> None:
    task = base / "quality-gate-pass"
    base_flow(task)
    report = read(task / "state" / "quality-report.json")
    assert "metrics" in report


def fixture_12(base: Path) -> None:
    task = base / "quality-gate-fail"
    base_flow(task, include_rag=False, allow_fail=True)
    report = read(task / "state" / "quality-report.json")
    assert report["status"] == "failed"


def fixture_13(_base: Path) -> None:
    code, data = run(["python3", "scripts/startup.py"])
    assert code == 0, data
    assert data["boundaries_blocked"]["cnki_wos_zotero_pdf_rag"] is True


def fixture_14(_base: Path) -> None:
    forbidden = ["ssh ", "localhost" + ":22", "openclaw" + "-cnki-takeover"]
    for folder in ["scripts", "agents"]:
        for path in (ROOT / folder).glob("**/*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                assert not any(token in text for token in forbidden), path


def fixture_15(base: Path) -> None:
    task = base / "multi-round-closure"
    base_flow(task)
    delivery = task / "delivery"
    assert (delivery / "handoff_to_writing.json").exists()
    assert (delivery / "human_review_needed.json").exists()
    handoff = read(delivery / "handoff_to_writing.json")
    assert "unresolved_critical_claims" in handoff
    assert "existing_references_merge_status" in handoff


def fixture_16(base: Path) -> None:
    task = base / "full-intake-completion-schema"
    code, data = run(["python3", "scripts/startup.py", "--task-dir", str(task)])
    assert code == 0, data
    code, data = run(["python3", "scripts/apply-intake-completion.py", "--task-dir", str(task), "--completion", str(FULL_COMPLETION)])
    assert code == 0, data
    intake = read(task / "state" / "intake-status.json")
    assert len(intake["results"]) == 3
    assert intake["results"][0]["kb_routing"]["target_kb"] == "B"
    assert intake["pool_avg_usable_text_chars"] == 113.33
    assert intake["pool_material_status"] == "insufficient"


def fixture_17(base: Path) -> None:
    task = base / "search-intake-call-package"
    base_flow(task)
    code, data = run(["python3", "scripts/build-search-intake-call.py", "--task-dir", str(task), "--batch-id", "batch-01"])
    assert code == 0, data
    package = read(task / "state" / "search-intake-calls" / "batch-01.json")
    assert package["target_skill"] == "检索入库"
    assert package["execution_status"] == "prepared_not_executed"
    assert (task / "state" / "search-intake-calls" / "batch-01.prompt.md").exists()


def fixture_18(base: Path) -> None:
    task = base / "post-ingestion-rag-call"
    base_flow(task)
    code, data = run(["python3", "scripts/build-post-ingestion-rag-call.py", "--task-dir", str(task), "--batch-id", "post-ingestion-01"])
    assert code == 0, data
    package = read(task / "state" / "rag-calls" / "post-ingestion-01.json")
    assert package["target_system"] == "RAG platform"
    assert package["claims"]


def fixture_19(base: Path) -> None:
    task = base / "post-ingestion-evidence-closure"
    base_flow(task)
    code, data = run(["python3", "scripts/build-post-ingestion-rag-call.py", "--task-dir", str(task), "--batch-id", "post-ingestion-01"])
    assert code == 0, data
    request = task / "state" / "rag-calls" / "post-ingestion-01.json"
    code, data = run(["python3", "scripts/validate-rag-response.py", "--task-dir", str(task), "--request", str(request), "--response", str(POST_INGESTION_RAG)])
    assert code == 0, data
    code, data = run(["python3", "scripts/build-evidence-map.py", "--task-dir", str(task)])
    assert code == 0, data
    evidence = read(task / "state" / "evidence-map.json")
    claim = next(item for item in evidence["claim_evidence"] if item["claim_id"] == "c-009")
    assert claim["evidence_status"] == "strong_support"
    assert claim["candidates"][0]["reference"]["ref_id"] == "ref-004"
    code, data = run(["python3", "scripts/build-footnote-candidate-pool.py", "--task-dir", str(task)])
    assert code == 0, data
    code, data = run(["python3", "scripts/prune-footnotes.py", "--task-dir", str(task)])
    assert code == 0, data
    code, data = run(["python3", "scripts/prune-references.py", "--task-dir", str(task)])
    assert code == 0, data
    code, data = run(["python3", "scripts/plan-footnotes.py", "--task-dir", str(task)])
    assert code == 0, data
    plan = read(task / "state" / "insertion-plan.json")
    assert any(item["claim_id"] == "c-009" for item in plan["insertions"])


def synthetic_pool(count: int = 20) -> dict:
    candidates = []
    for idx in range(1, count + 1):
        candidates.append({
            "candidate_id": f"fnc-{idx:03d}",
            "claim_id": f"c-{idx:03d}",
            "claim_type": "theoretical_claim",
            "need_level": "critical" if idx <= 4 else "important",
            "text": f"模拟论断 {idx}",
            "target_location": {"paragraph_id": "p-001", "sentence_id": f"s-{idx:03d}"},
            "reference": {"ref_id": f"ref-{idx:03d}", "title": f"模拟文献{idx}", "authors": ["作者"], "year": 2024, "source": "模拟期刊", "pages": "1-20"},
            "note_type": "footnote",
            "annotation_purpose": "source_anchor" if idx <= 4 else "evidence",
            "support_strength": "strong_support",
            "confidence": 0.9,
            "risks": [],
            "usable_text_chars": 260,
            "usable_text_source": "fixture",
            "material_flag": "normal",
            "necessity_score": 100 - idx,
            "candidate_note_text": f"模拟脚注补充内容 {idx}",
            "authenticity_status": "not_checked",
        })
    return {"article_id": "synthetic", "target_candidate_range": {"min": 15, "max": 25}, "candidates": candidates, "rejected_before_pool": []}


def fixture_20(base: Path) -> None:
    task = base / "usable-text-material-flags"
    code, data = run(["python3", "scripts/startup.py", "--task-dir", str(task)])
    assert code == 0, data
    code, data = run(["python3", "scripts/apply-intake-completion.py", "--task-dir", str(task), "--completion", str(FULL_COMPLETION)])
    assert code == 0, data
    intake = read(task / "state" / "intake-status.json")
    assert intake["results"][1]["material_flag"] == "below_average"
    assert intake["results"][2]["material_flag"] == "very_low"


def fixture_21(base: Path) -> None:
    task = base / "prune-20-to-15"
    write(task / "state" / "footnote-candidate-pool.json", synthetic_pool(20))
    code, data = run(["python3", "scripts/prune-footnotes.py", "--task-dir", str(task), "--target", "15"])
    assert code == 0, data
    pruning = read(task / "state" / "footnote-pruning-result.json")
    assert len(pruning["kept"]) == 15
    assert len(pruning["removed"]) == 5


def fixture_22(base: Path) -> None:
    task = base / "prune-background-vacuous"
    pool = synthetic_pool(3)
    pool["candidates"][0]["annotation_purpose"] = "background"
    pool["candidates"][0]["necessity_score"] = 30
    write(task / "state" / "footnote-candidate-pool.json", pool)
    code, data = run(["python3", "scripts/prune-footnotes.py", "--task-dir", str(task), "--target", "2"])
    assert code == 0, data
    removed = read(task / "state" / "footnote-pruning-result.json")["removed"]
    assert any(item["pruning_reason"] == "background_without_necessary_supplement" for item in removed)


def fixture_23(base: Path) -> None:
    task = base / "reference-only-barred"
    pool = synthetic_pool(1)
    pool["candidates"][0]["annotation_purpose"] = "reference_only"
    pool["candidates"][0]["note_type"] = "footnote"
    write(task / "state" / "footnote-candidate-pool.json", pool)
    code, data = run(["python3", "scripts/prune-footnotes.py", "--task-dir", str(task)])
    assert code == 0, data
    assert read(task / "state" / "footnote-pruning-result.json")["removed"][0]["pruning_reason"] == "reference_only_barred_from_footnote_body"


def fixture_24(base: Path) -> None:
    task = base / "reference-prune-30"
    write(task / "state" / "footnote-candidate-pool.json", synthetic_pool(35))
    code, data = run(["python3", "scripts/prune-references.py", "--task-dir", str(task), "--target-max", "30"])
    assert code == 0, data
    plan = read(task / "state" / "reference-pruning-plan.json")
    assert len(plan["kept_references"]) == 30


def fixture_25(base: Path) -> None:
    task = base / "authenticity-request-result"
    base_flow(task)
    request = read(task / "state" / "authenticity-verification-request.json")
    result_data = read(task / "state" / "authenticity-verification-result.json")
    assert request["execution_status"] == "prepared_not_executed"
    assert result_data["issues"]


def fixture_26(base: Path) -> None:
    task = base / "authenticity-conflict-blocks"
    base_flow(task)
    bad = read(task / "state" / "authenticity-verification-result.json")
    bad["results"][0]["authenticity_status"] = "failed"
    bad["results"][0]["risks"] = ["pdf_rag_conflict"]
    write(task / "bad-auth.json", bad)
    code, data = run(["python3", "scripts/apply-authenticity-verification-result.py", "--task-dir", str(task), "--verification", str(task / "bad-auth.json")])
    assert code == 0, data
    code, data = run(["python3", "scripts/validate-note-reference-consistency.py", "--task-dir", str(task), "--allow-fail"])
    assert code == 0, data
    gate = read(task / "state" / "consistency-gate-result.json")
    assert gate["status"] == "failed"


def fixture_27(base: Path) -> None:
    task = base / "wrong-position-risk"
    base_flow(task)
    bad = read(task / "state" / "authenticity-verification-result.json")
    bad["results"][0]["authenticity_status"] = "human_review"
    bad["results"][0]["risks"] = ["wrong_insertion_position"]
    write(task / "position-auth.json", bad)
    code, data = run(["python3", "scripts/apply-authenticity-verification-result.py", "--task-dir", str(task), "--verification", str(task / "position-auth.json")])
    assert code == 0, data
    issues = read(task / "state" / "authenticity-issues.json")["issues"]
    assert any("wrong_insertion_position" in item["risks"] for item in issues)


def fixture_28(base: Path) -> None:
    task = base / "unconsumed-reference-warning"
    base_flow(task)
    plan = read(task / "state" / "insertion-plan.json")
    plan["reference_list"]["new_references"].append({"ref_id": "ref-unused", "title": "未消费文献"})
    write(task / "state" / "insertion-plan.json", plan)
    code, data = run(["python3", "scripts/validate-note-reference-consistency.py", "--task-dir", str(task), "--allow-fail"])
    assert code == 0, data
    gate = read(task / "state" / "consistency-gate-result.json")
    assert "ref-unused" in ",".join(gate["warnings"])


def fixture_29(base: Path) -> None:
    task = base / "delivery-includes-authenticity"
    base_flow(task)
    assert (task / "delivery" / "authenticity-verification-request.json").exists()
    assert (task / "delivery" / "consistency-gate-result.json").exists()


def fixture_30(base: Path) -> None:
    task = base / "retrieval-first-blocks-rag-without-intake"
    for step in [
        ["python3", "scripts/startup.py", "--task-dir", str(task)],
        ["python3", "scripts/article-intake.py", "--task-dir", str(task), "--file", str(ARTICLE)],
        ["python3", "scripts/claim-segmentation.py", "--task-dir", str(task)],
        ["python3", "scripts/citation-need-diagnosis.py", "--task-dir", str(task)],
    ]:
        code, data = run(step)
        assert code == 0, data
    code, data = run(["python3", "scripts/build-rag-request.py", "--task-dir", str(task)])
    assert code != 0
    assert "intake-status.json" in "".join(data.get("errors", []))


def fixture_31(base: Path) -> None:
    task = base / "blueprint-generates-directions"
    prepare_blueprint(task)
    bp = read(task / "state" / "search-blueprint.json")
    assert len(bp["directions"]) >= 3
    assert bp["type_coverage_minimum"] == 3
    assert all("keywords_zh" in item and "source_types" in item for item in bp["directions"])


def fixture_32(base: Path) -> None:
    task = base / "initial-library-handoff-from-blueprint"
    prepare_blueprint(task)
    code, data = run(["python3", "scripts/build-initial-search-handoff.py", "--task-dir", str(task)])
    assert code == 0, data
    handoff = read(task / "state" / "search-intake-requests" / "initial-library.json")
    assert handoff["request_type"] == "search_intake_library_build"
    assert handoff["library_requirements"]["initial_pool_min_sources"] == 40


def fixture_33(base: Path) -> None:
    task = base / "initial-library-call-package"
    prepare_initial_call(task)
    pkg = read(task / "state" / "search-intake-calls" / "initial-library.json")
    assert pkg["handoff"]["request_type"] == "search_intake_library_build"
    prompt = (task / "state" / "search-intake-calls" / "initial-library.prompt.md").read_text(encoding="utf-8")
    assert "初始文献库建设" in prompt


def fixture_34(base: Path) -> None:
    task = base / "intake-quality-gate-pass"
    prepare_initial_call(task)
    code, data = run(["python3", "scripts/apply-intake-completion.py", "--task-dir", str(task), "--completion", str(INITIAL_COMPLETION)])
    assert code == 0, data
    code, data = run(["python3", "scripts/validate-intake-quality.py", "--task-dir", str(task)])
    assert code == 0, data
    gate = read(task / "state" / "intake-quality-gate.json")
    assert gate["status"] == "passed"


def fixture_35(base: Path) -> None:
    task = base / "intake-quality-gate-fail-pool-size"
    prepare_initial_call(task)
    code, data = run(["python3", "scripts/apply-intake-completion.py", "--task-dir", str(task), "--completion", str(INITIAL_COMPLETION_SMALL)])
    assert code == 0, data
    code, data = run(["python3", "scripts/validate-intake-quality.py", "--task-dir", str(task), "--allow-fail"])
    assert code == 0, data
    assert read(task / "state" / "intake-quality-gate.json")["status"] == "failed"


def fixture_36(base: Path) -> None:
    task = base / "intake-quality-gate-fail-material"
    prepare_initial_call(task)
    code, data = run(["python3", "scripts/apply-intake-completion.py", "--task-dir", str(task), "--completion", str(INITIAL_COMPLETION_LOW)])
    assert code == 0, data
    code, data = run(["python3", "scripts/validate-intake-quality.py", "--task-dir", str(task), "--allow-fail"])
    assert code == 0, data
    assert any("usable text" in item for item in read(task / "state" / "intake-quality-gate.json")["blocking"])


def fixture_37(base: Path) -> None:
    task = base / "intake-quality-gate-fail-type-coverage"
    prepare_initial_call(task)
    code, data = run(["python3", "scripts/apply-intake-completion.py", "--task-dir", str(task), "--completion", str(INITIAL_COMPLETION_NARROW)])
    assert code == 0, data
    code, data = run(["python3", "scripts/validate-intake-quality.py", "--task-dir", str(task), "--allow-fail"])
    assert code == 0, data
    assert read(task / "state" / "intake-quality-gate.json")["metrics"]["type_coverage"] == 1


def fixture_38(base: Path) -> None:
    task = base / "full-retrieval-first-flow"
    base_flow_retrieval_first(task)
    assert (task / "delivery" / "search-blueprint.json").exists()
    assert (task / "delivery" / "intake-quality-gate.json").exists()


def fixture_39(base: Path) -> None:
    task = base / "gap-round2-after-initial-library"
    base_flow_retrieval_first(task)
    handoff = read(task / "state" / "search-intake-requests" / "gap-round2.json")
    assert handoff["macro_round"] == "round2"
    assert all(req["search_strategy"]["constraints"]["target_kb"] == "C" for req in handoff["requests"])


def fixture_40(base: Path) -> None:
    task = base / "validate-citation-plan-blocks-without-blueprint"
    base_flow(task, allow_fail=True)
    code, data = run(["python3", "scripts/validate-citation-plan.py", "--task-dir", str(task), "--allow-fail"])
    assert code == 0, data
    report = read(task / "state" / "quality-report.json")
    assert any("retrieval blueprint missing" in item for item in report["blocking_issues"])


def fixture_41(base: Path) -> None:
    task = base / "delivery-includes-blueprint-and-intake-gate"
    base_flow_retrieval_first(task)
    assert (task / "delivery" / "search-blueprint.json").exists()
    assert (task / "delivery" / "intake-quality-gate.json").exists()


FIXTURES = [
    fixture_01, fixture_02, fixture_03, fixture_04, fixture_05,
    fixture_06, fixture_07, fixture_08, fixture_09, fixture_10,
    fixture_11, fixture_12, fixture_13, fixture_14, fixture_15,
    fixture_16,
    fixture_17, fixture_18,
    fixture_19,
    fixture_20, fixture_21, fixture_22, fixture_23, fixture_24,
    fixture_25, fixture_26, fixture_27, fixture_28, fixture_29,
    fixture_30, fixture_31, fixture_32, fixture_33, fixture_34,
    fixture_35, fixture_36, fixture_37, fixture_38, fixture_39,
    fixture_40, fixture_41,
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--fixture")
    args = parser.parse_args()
    if not args.all and not args.fixture:
        parser.error("use --all or --fixture")
    with tempfile.TemporaryDirectory(prefix="reference-footnote-fixtures-") as tmp:
        base = Path(tmp)
        results = []
        selected = FIXTURES
        if args.fixture:
            idx = int(args.fixture)
            selected = [FIXTURES[idx - 1]]
        for idx, fn in enumerate(selected, start=1):
            fn(base)
            results.append({"fixture": f"fixture-{idx:02d}", "status": "passed"})
    print(json.dumps({"status": "passed", "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
