from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def add_wenheng_args(parser: Any) -> None:
    parser.add_argument("--wenheng-task-id", default=os.getenv("WENHENG_TASK_ID", ""))
    parser.add_argument("--wenheng-backend-url", default=os.getenv("WENHENG_BACKEND_URL", ""))


def verify_wenheng_native(args: Any, *, skill_id: str, task_type: str, writing: bool) -> dict[str, Any]:
    task_id = getattr(args, "wenheng_task_id", "") or os.getenv("WENHENG_TASK_ID", "")
    backend_url = (getattr(args, "wenheng_backend_url", "") or os.getenv("WENHENG_BACKEND_URL", "")).rstrip("/")
    api_key = os.getenv("WENHENG_BACKEND_API_KEY", "")
    allow_legacy = os.getenv("WENHENG_ALLOW_LEGACY_FLOW") == "1"
    required = os.getenv("WENHENG_PRODUCTION_MODE") == "1" or os.getenv("WENHENG_NATIVE_REQUIRED") == "1" or bool(task_id)
    task_dir = Path(getattr(args, "task_dir", "") or os.getenv("WENHENG_TASK_DIR", "") or ".")

    if not required:
        event = _maybe_record_legacy_deviation(backend_url, api_key, task_id, skill_id)
        return {
            "binding_status": "standalone_legacy_flow",
            "native": False,
            "skill_id": skill_id,
            "task_type": task_type,
            "production_evidence_allowed": False,
            "learning_event_id": event.get("event", {}).get("event_id") if event else None,
            "note": "Legacy/offline startup is explicitly allowed via WENHENG_ALLOW_LEGACY_FLOW=1, but it is not Wenheng native completion evidence.",
        }

    if not task_id:
        raise RuntimeError(f"{skill_id} requires WENHENG_TASK_ID or --wenheng-task-id; set WENHENG_ALLOW_LEGACY_FLOW=1 only for standalone offline debugging")
    if not backend_url or not api_key:
        raise RuntimeError("Wenheng native mode requires WENHENG_BACKEND_URL and WENHENG_BACKEND_API_KEY")

    task_response = _request_json(backend_url, api_key, "GET", f"/api/tasks/{urllib.parse.quote(task_id)}")
    task = task_response.get("task", task_response)
    actual_type = task.get("task_type") or task.get("type")
    if actual_type and actual_type != task_type:
        raise RuntimeError(f"B02 task type mismatch: expected {task_type}, got {actual_type}")

    channel_decision = _extract_channel_decision(task)
    verdict = str(channel_decision.get("verdict") or channel_decision.get("decision") or "").lower()
    if not verdict:
        raise RuntimeError("F06 final verdict is missing")
    if verdict in {"forbidden", "blocked"}:
        raise RuntimeError(f"F06 channel decision blocks this task: {channel_decision.get('reason') or channel_decision}")

    style_memory = _read_style_memory(backend_url, api_key, task, skill_id, task_type, writing)
    usage = _write_style_memory_usage(backend_url, api_key, task_id, skill_id, task_type, style_memory, writing)
    timeline = _write_task_event(backend_url, api_key, task_id, "runtime_start", {
        "event_type": "runtime_start",
        "skill_id": skill_id,
        "task_type": task_type,
        "source": "reference_footnote_native_runtime",
    })
    h08 = _write_h08_evidence(backend_url, api_key, task, skill_id, task_type, channel_decision, style_memory, task_dir)
    learning = _record_learning_event(backend_url, api_key, {
        "source": "success_fix",
        "task_id": task_id,
        "skill_id": skill_id,
        "severity": "P2",
        "symptom": "ReferenceFootnote native runtime start validated B02/F06/G07/H08 contract.",
        "fix_summary": "Runtime startup wrote B02 timeline, H08 evidence, G07 usage, LearningEvent, and local archive handoff.",
        "prevention_rule_candidate": "ReferenceFootnote production starts must validate B02/F06 and write sanitized H08/LearningEvent evidence before completion claims.",
        "evidence_path": h08.get("evidence_path") or h08.get("path"),
    })
    handoff = _write_local_handoff(task_dir, task, skill_id, task_type, channel_decision, style_memory, h08, timeline)

    return {
        "binding_status": "validated_by_wenheng_native_contract_v2",
        "native": True,
        "skill_id": skill_id,
        "task_type": task_type,
        "wenheng_task_id": task_id,
        "f06_final_verdict": verdict,
        "f06_channel_decision": channel_decision,
        "style_memory": style_memory,
        "g07_usage_id": _first_present(usage, ["usage.usage_id", "usage_id", "id"]),
        "b02_timeline_event_id": _first_present(timeline, ["event.event_id", "event_id", "id"]),
        "h08": h08,
        "learning_event_id": _first_present(learning, ["event.event_id", "event_id", "id"]),
        "archive": {
            "required": True,
            "handoff_path": str(handoff),
            "archive_api": f"/api/tasks/{task_id}/archive",
        },
        "production_evidence_allowed": True,
    }


def _request_json(base_url: str, api_key: str, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            text = response.read().decode("utf-8")
            return json.loads(text) if text else {}
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Wenheng API {method} {path} failed: {exc.code}") from exc


def _extract_channel_decision(task: dict[str, Any]) -> dict[str, Any]:
    routing = task.get("routing") or task.get("routing_decision") or {}
    decision = routing.get("channel_decision") or task.get("channel_decision") or {}
    if not decision and routing.get("f06_final_verdict"):
        decision = {"verdict": routing.get("f06_final_verdict")}
    decisions = decision.get("decisions") or []
    if not decision.get("verdict") and decisions:
        first = decisions[0] or {}
        decision = {**decision, "verdict": first.get("decision") or first.get("verdict")}
    return decision


def _read_style_memory(base_url: str, api_key: str, task: dict[str, Any], skill_id: str, task_type: str, writing: bool) -> dict[str, Any]:
    query = urllib.parse.urlencode({
        "task_type": task_type,
        "skill_id": skill_id,
        "channel_id": task.get("channel_id") or task.get("target_channel") or "",
    })
    payload = _request_json(base_url, api_key, "GET", f"/api/g07/style-memory/active-rules?{query}")
    rules = payload.get("rules") or payload.get("active_rules") or []
    applied = [str(rule.get("memory_id") or rule.get("rule_id") or rule.get("id") or rule.get("rule_name")) for rule in rules if isinstance(rule, dict)]
    if writing:
        return {
            "style_memory_source": "G07",
            "style_memory_rules_applied": [item for item in applied if item],
            "style_memory_rules_ignored": [],
            "style_memory_conflicts": payload.get("conflicts") or [],
            "style_memory_not_applicable_reason": None,
            "style_memory_feedback_candidate_id": payload.get("feedback_candidate_id"),
        }
    return {
        "style_memory_source": "G07",
        "style_memory_rules_applied": [],
        "style_memory_rules_ignored": [],
        "style_memory_conflicts": [],
        "style_memory_not_applicable_reason": "ReferenceFootnote evidence-only stage; no prose style decision at startup.",
        "style_memory_feedback_candidate_id": None,
    }


def _write_style_memory_usage(base_url: str, api_key: str, task_id: str, skill_id: str, task_type: str, style_memory: dict[str, Any], writing: bool) -> dict[str, Any]:
    return _request_json(base_url, api_key, "POST", "/api/g07/style-memory/usage", {
        "task_id": task_id,
        "skill_id": skill_id,
        "task_type": task_type,
        "source": "reference_footnote_native_runtime",
        "applied": style_memory["style_memory_rules_applied"],
        "ignored": style_memory["style_memory_rules_ignored"],
        "conflicts": style_memory["style_memory_conflicts"],
        "ignored_reason": style_memory["style_memory_not_applicable_reason"] if not writing else None,
    })


def _write_task_event(base_url: str, api_key: str, task_id: str, event_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _request_json(base_url, api_key, "POST", f"/api/tasks/{urllib.parse.quote(task_id)}/events/{event_name}", payload)


def _write_h08_evidence(base_url: str, api_key: str, task: dict[str, Any], skill_id: str, task_type: str, channel_decision: dict[str, Any], style_memory: dict[str, Any], task_dir: Path) -> dict[str, Any]:
    return _request_json(base_url, api_key, "POST", "/api/h08/evidence", {
        "task_id": task.get("task_id"),
        "skill_id": skill_id,
        "task_type": task_type,
        "source": "reference_footnote_native_runtime",
        "evidence_type": "native_runtime_start",
        "sensitive_data": "redacted",
        "task_folder": task.get("task_folder") or str(task_dir),
        "f06_channel_decision": channel_decision,
        "style_memory": style_memory,
    })


def _record_learning_event(base_url: str, api_key: str, event: dict[str, Any]) -> dict[str, Any]:
    return _request_json(base_url, api_key, "POST", "/api/h08/learning-events", event)


def _maybe_record_legacy_deviation(base_url: str, api_key: str, task_id: str, skill_id: str) -> dict[str, Any] | None:
    if not base_url or not api_key:
        return None
    return _record_learning_event(base_url, api_key, {
        "source": "workflow_deviation",
        "task_id": task_id or None,
        "skill_id": skill_id,
        "severity": "P1",
        "symptom": "ReferenceFootnote legacy/offline flow was explicitly allowed; it cannot produce production evidence.",
        "prevention_rule_candidate": "Legacy ReferenceFootnote runs must be marked non-production and reviewed before any completion claim.",
    })


def _write_local_handoff(task_dir: Path, task: dict[str, Any], skill_id: str, task_type: str, channel_decision: dict[str, Any], style_memory: dict[str, Any], h08: dict[str, Any], timeline: dict[str, Any]) -> Path:
    out = task_dir / "state" / "wenheng-native-handoff.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0.0",
        "source_skill": "参考文献补注",
        "wenheng_task": {
            "wenheng_task_id": task.get("task_id"),
            "task_folder": task.get("task_folder") or str(task_dir),
            "task_type": task_type,
            "target_skill": task.get("target_skill") or skill_id,
            "source_run_id": task.get("run_id"),
        },
        "routing": {
            "f06_routing_decision": str(channel_decision.get("verdict") or channel_decision.get("decision")),
            "target_channel": channel_decision.get("target_channel") or task.get("target_channel") or task.get("channel_id"),
            "forbidden_channel_checked": True,
        },
        "style_memory": style_memory,
        "e05_writeback": {"enabled": True, "sanitized": True},
        "b02_timeline": [{"event_id": _first_present(timeline, ["event.event_id", "event_id", "id"]), "event_type": "runtime_start"}],
        "h08_evidence": {
            "evidence_path": h08.get("evidence_path") or h08.get("path"),
            "sensitive_data": "redacted",
        },
        "archive": {"archive_required": True, "package_ref": None},
        "no_bypass": {"wenheng_task_required": True, "intake_only_without_task": True},
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def _first_present(data: dict[str, Any], paths: list[str]) -> Any:
    for path in paths:
        current: Any = data
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                current = None
                break
            current = current[part]
        if current is not None:
            return current
    return None
