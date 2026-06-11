#!/usr/bin/env python3
"""Execute a post-2.5 RAG reverse lookup and write the internal response artifact."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib import error, request as urlrequest

from reflib import ROOT, ensure_task, print_json, read_json, result, update_flow_status, write_json


DEFAULT_CONFIG = ROOT / "config" / "rag-executor.yaml"


def yaml_scalar(value: str):
    value = value.strip()
    if value in {"null", "~", ""}:
        return None
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return [item.strip() for item in value[1:-1].split(",") if item.strip()]
    try:
        return int(value)
    except ValueError:
        return value.strip("\"'")


def read_simple_yaml(path: Path) -> dict:
    """Parse the small config subset used by config/rag-executor.yaml."""
    data: dict = {}
    stack: list[tuple[int, dict]] = [(-1, data)]
    current_list_key: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if line.startswith("- ") and current_list_key:
            parent.setdefault(current_list_key, []).append(yaml_scalar(line[2:]))
            continue
        current_list_key = None
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parsed = yaml_scalar(value)
            parent[key] = parsed
            if parsed == []:
                current_list_key = key
    return data


def load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    if path.suffix.lower() == ".json":
        return read_json(path)
    return read_simple_yaml(path)


def kb_ids_from(task: Path, request_payload: dict, call_payload: dict | None, config: dict) -> list[str]:
    override = ((config.get("kb_routing") or {}).get("override_kb_ids") or [])
    if override:
        return [str(x) for x in override]
    intake_path = task / "state" / "intake-status.json"
    if intake_path.exists():
        intake = read_json(intake_path)
        for key in ("kb_ids", "ready_kb_ids"):
            values = intake.get(key)
            if isinstance(values, list) and values:
                return [str(x) for x in values]
        found: list[str] = []
        for item in intake.get("results", []):
            routing = item.get("kb_routing") or {}
            for value in (routing.get("kb_id"), routing.get("rag_index"), routing.get("target_kb")):
                if value and str(value) not in found:
                    found.append(str(value))
        if found:
            return found
    if call_payload:
        values = ((call_payload.get("kb_context") or {}).get("kb_ids") or [])
        if values:
            return [str(x) for x in values]
    values = (request_payload.get("kb_context") or {}).get("kb_ids") or []
    return [str(x) for x in values]


def synthesize_mock_response(request_payload: dict, kb_ids: list[str]) -> dict:
    results = []
    for claim in request_payload.get("claims", []):
        need = claim.get("need_level")
        if need not in {"critical", "important", "recommended"}:
            candidates = []
        else:
            strength = "strong_support" if need in {"critical", "important"} else "partial_support"
            candidates = [{
                "candidate_id": f"mock-{claim.get('claim_id')}",
                "reference": {
                    "ref_id": "mock-ref-001",
                    "title": "RAG mock source for offline reverse lookup",
                    "authors": ["ReferenceFootnote Fixture"],
                    "year": 2026,
                    "source": "offline fixture",
                    "pages": "1-10",
                },
                "support_assessment": {
                    "strength": strength,
                    "confidence": 0.8 if strength == "strong_support" else 0.62,
                    "reasoning": "Mock executor output for offline gate; not a real citation.",
                },
                "match_details": {
                    "snippet": f"Mock chunk for {claim.get('claim_id')}: {claim.get('text', '')[:80]}",
                    "snippet_page": 1,
                    "kb_ids": kb_ids,
                },
                "chunk_text": f"Mock chunk for {claim.get('claim_id')}: {claim.get('text', '')[:120]}",
                "kb_id": kb_ids[0] if kb_ids else "mock-kb",
                "risks": [],
            }]
        results.append({"claim_id": claim.get("claim_id"), "status": "completed", "candidates": candidates})
    return {
        "protocol_version": request_payload.get("protocol_version", "1.0"),
        "response_type": "reverse_lookup_result",
        "batch_id": request_payload.get("batch_id"),
        "executor": {"mode": "mock", "kb_ids": kb_ids},
        "results": results,
    }


def read_mock_response(path: Path, request_payload: dict, kb_ids: list[str]) -> dict:
    if not path.exists():
        return synthesize_mock_response(request_payload, kb_ids)
    response = read_json(path)
    response["batch_id"] = request_payload.get("batch_id")
    response.setdefault("protocol_version", "1.0")
    response.setdefault("response_type", "reverse_lookup_result")
    response.setdefault("executor", {"mode": "mock", "kb_ids": kb_ids})
    return response


def missing_live_config(config: dict) -> list[str]:
    live = config.get("live") or {}
    missing = []
    for field in ((config.get("blocker_policy") or {}).get("required_for_live") or ["base_url", "api_key_env", "model"]):
        value = live.get(field)
        if not value:
            missing.append(field)
        elif field == "api_key_env" and not os.environ.get(str(value), "").strip():
            missing.append(f"env:{value}")
    return missing


def call_live(config: dict, request_payload: dict, kb_ids: list[str]) -> dict:
    live = config.get("live") or {}
    endpoint = str(live["base_url"]).rstrip("/") + str(live.get("route") or "/chat/completions")
    api_key = os.environ[str(live["api_key_env"])]
    prompt = {
        "task": "ReferenceFootnote RAG reverse lookup",
        "kb_ids": kb_ids,
        "return_contract": "Return JSON with response_type=reverse_lookup_result, batch_id, results[].claim_id, results[].candidates[].support_assessment, match_details.",
        "request": request_payload,
    }
    payload = {
        "model": live["model"],
        "messages": [
            {"role": "system", "content": "You are a closed-library RAG reverse lookup executor. Return strict JSON only."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    req = urlrequest.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=int(live.get("timeout_seconds") or 60)) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"RAG reverse lookup HTTP {exc.code}: {body[:1000]}") from exc
    parsed = json.loads(raw)
    content = (((parsed.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
    response = json.loads(content)
    response.setdefault("protocol_version", request_payload.get("protocol_version", "1.0"))
    response.setdefault("response_type", "reverse_lookup_result")
    response.setdefault("batch_id", request_payload.get("batch_id"))
    response.setdefault("executor", {"mode": "live", "kb_ids": kb_ids})
    return response


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--batch-id", default="batch-01")
    parser.add_argument("--config-path", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--mock", action="store_true", help="force mock executor and never call the live RAG API")
    parser.add_argument("--mock-response", type=Path, help="optional mock response JSON; if omitted, a synthetic response is generated")
    args = parser.parse_args()
    task = ensure_task(args.task_dir)
    call_path = task / "state" / "rag-calls" / f"{args.batch_id}.json"
    request_path = task / "state" / "rag-requests" / f"{args.batch_id}.json"
    source_path = request_path if request_path.exists() else call_path
    if not source_path.exists():
        print_json(result("failed", errors=[f"RAG request missing: {request_path} or {call_path}"]))
        return 1
    config = load_config(args.config_path)
    request_payload = read_json(source_path)
    request_payload.setdefault("request_type", request_payload.get("call_type", "reverse_lookup"))
    request_payload.setdefault("batch_id", args.batch_id)
    call_payload = read_json(call_path) if call_path.exists() else None
    kb_ids = kb_ids_from(task, request_payload, call_payload, config)
    mode = "mock" if args.mock else (((config.get("executor") or {}).get("mode")) or "mock")

    if mode == "mock":
        mock_path = args.mock_response
        if mock_path is None:
            mock_dir = ROOT / ((config.get("executor") or {}).get("mock_response_dir") or "tests/fixtures/mocks")
            mock_path = mock_dir / f"{args.batch_id}.response.json"
        response = read_mock_response(mock_path, request_payload, kb_ids)
    elif mode == "live":
        missing = missing_live_config(config)
        if missing:
            update_flow_status(task, "S50b", status="blocked", blocked=True, note="missing_rag_executor_config")
            out = result("failed", blocker="missing_rag_executor_config", missing=missing, message="RAG reverse lookup executor config is incomplete; no user 回执 is requested.")
            print_json(out)
            return 1
        try:
            response = call_live(config, request_payload, kb_ids)
        except Exception as exc:
            update_flow_status(task, "S50b", status="blocked", blocked=True, note="rag_reverse_lookup_failed")
            print_json(result("failed", blocker="rag_reverse_lookup_failed", errors=[str(exc)]))
            return 1
    else:
        print_json(result("failed", errors=[f"unsupported RAG executor mode: {mode}"]))
        return 1

    out_path = task / "state" / "rag-calls" / f"{args.batch_id}.response.json"
    write_json(out_path, response)
    update_flow_status(task, "S50b", note=f"rag reverse lookup response written: {out_path}")
    print_json(result("passed", output=str(out_path), mode=mode, kb_ids=kb_ids, results=len(response.get("results", []))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
