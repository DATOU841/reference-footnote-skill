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


def run(args: list[str]) -> tuple[int, dict]:
    proc = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {"stdout": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, data


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def base_flow(task: Path, *, include_rag: bool = True, allow_fail: bool = True) -> None:
    steps = [
        ["python3", "scripts/startup.py", "--task-dir", str(task)],
        ["python3", "scripts/article-intake.py", "--task-dir", str(task), "--file", str(ARTICLE)],
        ["python3", "scripts/claim-segmentation.py", "--task-dir", str(task)],
        ["python3", "scripts/citation-need-diagnosis.py", "--task-dir", str(task)],
        ["python3", "scripts/build-rag-request.py", "--task-dir", str(task), "--batch-id", "batch-01"],
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
    code, data = run(["python3", "scripts/build-search-handoff.py", "--task-dir", str(task), "--batch-id", "batch-01"])
    assert code == 0, data
    code, data = run(["python3", "scripts/apply-intake-completion.py", "--task-dir", str(task), "--completion", str(COMPLETION)])
    assert code == 0, data
    code, data = run(["python3", "scripts/plan-footnotes.py", "--task-dir", str(task)])
    assert code == 0, data
    cmd = ["python3", "scripts/validate-citation-plan.py", "--task-dir", str(task)]
    if allow_fail:
        cmd.append("--allow-fail")
    code, data = run(cmd)
    assert code == 0, data
    code, data = run(["python3", "scripts/build-delivery.py", "--task-dir", str(task)])
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
    code, data = run(["python3", "scripts/plan-footnotes.py", "--task-dir", str(task)])
    assert code == 0, data
    plan = read(task / "state" / "insertion-plan.json")
    assert any(item["claim_id"] == "c-009" for item in plan["insertions"])


FIXTURES = [
    fixture_01, fixture_02, fixture_03, fixture_04, fixture_05,
    fixture_06, fixture_07, fixture_08, fixture_09, fixture_10,
    fixture_11, fixture_12, fixture_13, fixture_14, fixture_15,
    fixture_16,
    fixture_17, fixture_18,
    fixture_19,
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
