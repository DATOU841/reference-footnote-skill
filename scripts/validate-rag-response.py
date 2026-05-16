#!/usr/bin/env python3
"""Validate and interpret an offline RAG reverse lookup response."""

from __future__ import annotations

import argparse
from pathlib import Path
from reflib import RISK_FLAGS, SUPPORT_STRENGTHS, ensure_task, print_json, read_json, result, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--response", required=True, type=Path)
    args = parser.parse_args()
    ensure_task(args.task_dir)
    errors = []
    request = read_json(args.request)
    response = read_json(args.response)
    if response.get("response_type") != "reverse_lookup_result":
        errors.append("response_type must be reverse_lookup_result")
    if response.get("batch_id") != request.get("batch_id"):
        errors.append("batch_id mismatch")
    req_claims = {c["claim_id"] for c in request.get("claims", [])}
    interpretations = []
    for item in response.get("results", []):
        claim_id = item.get("claim_id")
        if claim_id not in req_claims:
            errors.append(f"unexpected claim_id: {claim_id}")
        candidates = item.get("candidates", [])
        if not candidates:
            interpretations.append({"claim_id": claim_id, "status": "no_support", "best_strength": "no_support", "candidates": [], "risks": []})
            continue
        interpreted = []
        for cand in candidates:
            assessment = cand.get("support_assessment", {})
            strength = assessment.get("strength")
            risks = cand.get("risks", []) or assessment.get("risks", [])
            if strength not in SUPPORT_STRENGTHS:
                errors.append(f"invalid support strength for {claim_id}: {strength}")
            unknown = [r for r in risks if r not in RISK_FLAGS]
            if unknown:
                errors.append(f"unknown risks for {claim_id}: {unknown}")
            if cand.get("match_details", {}).get("snippet_page") is None and strength in {"strong_support", "partial_support"} and "page_missing" not in risks:
                risks = [*risks, "page_missing"]
            interpreted.append({**cand, "risks": risks})
        best = interpreted[0]
        interpretations.append({
            "claim_id": claim_id,
            "status": "interpreted",
            "best_strength": best.get("support_assessment", {}).get("strength", "no_support"),
            "candidates": interpreted,
            "risks": best.get("risks", []),
        })
    out_data = {"batch_id": request.get("batch_id"), "interpretations": interpretations, "errors": errors}
    out = args.task_dir / "state" / "evidence-interpretations" / f"{request.get('batch_id')}.json"
    write_json(out, out_data)
    print_json(result("failed" if errors else "passed", output=str(out), errors=errors, interpreted=len(interpretations)))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
