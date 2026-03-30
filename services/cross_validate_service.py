import json
from pathlib import Path
from typing import Any

from evidence.graph_store import persist_evidence
from evidence.rule_engine import calculate_anomaly_score, run_consistency_checks
from execution.state_store import get_status
from settings import RECORDS_DIR
from storage import archive_stage_result, load_record_parsed_context


def _load_json(path: Path) -> dict[str, Any]:
    """读取 JSON 文件并返回字典。"""
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_file(record_dir: Path, pattern: str) -> Path | None:
    """按修改时间获取匹配模式的最新文件。"""
    files = sorted(record_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _load_execution_ids(record_dir: Path) -> list[str]:
    """从 execute 响应归档中提取 execution_id 列表。"""
    execute_resp = _latest_file(record_dir, "execute_resp*.json")
    if not execute_resp:
        return []
    data = _load_json(execute_resp)
    return [x.get("execution_id") for x in data.get("jobs", []) if x.get("execution_id")]


def _fallback_status_from_file(record_dir: Path, execution_id: str) -> dict[str, Any]:
    """当 Redis 无状态时，从本地状态快照文件兜底读取。"""
    f = _latest_file(record_dir, f"execution_status_{execution_id}*.json")
    if not f:
        return {}
    return _load_json(f)


def _collect_task_results(record_id: str, execution_ids: list[str]) -> list[dict[str, Any]]:
    """收集子任务执行结果并统一整理为验证输入。"""
    record_dir = RECORDS_DIR / record_id
    results: list[dict[str, Any]] = []

    for execution_id in execution_ids:
        status = get_status(execution_id)
        # Support demo mode where Redis may be reset and statuses only exist in local files.
        if not status:
            status = _fallback_status_from_file(record_dir, execution_id)
        if not status:
            continue

        payload = status.get("payload") or {}
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {"raw": payload}

        results.append(
            {
                "execution_id": execution_id,
                "task_type": status.get("task_type"),
                "status": status.get("status"),
                "updated_at": status.get("updated_at"),
                "confidence": payload.get("confidence"),
                "assigned_model": payload.get("assigned_model"),
                "assigned_tools": payload.get("assigned_tools", []),
                "payload": payload,
            }
        )
    return results


def cross_validate(record_id: str, execution_ids: list[str] | None = None, parsed_context: dict[str, Any] | None = None):
    """执行交叉验证、异常打分并生成可追溯证据链。"""
    record_dir = RECORDS_DIR / record_id
    if not record_dir.exists():
        raise FileNotFoundError(f"record not found: {record_id}")

    parsed = parsed_context or load_record_parsed_context(record_id)
    ids = execution_ids or _load_execution_ids(record_dir)
    task_results = _collect_task_results(record_id, ids)

    checks = run_consistency_checks(parsed, task_results)
    anomaly_score = calculate_anomaly_score(checks)

    conclusion = "通过"
    if anomaly_score >= 60:
        conclusion = "高风险，建议人工复核"
    elif anomaly_score >= 20:
        conclusion = "中等风险，建议抽样复核"

    evidence_chain = []
    for item in task_results:
        evidence_chain.append(
            {
                "who": item.get("assigned_model") or "unknown-model",
                "when": item.get("updated_at"),
                "task_type": item.get("task_type"),
                "rule_refs": [c.get("rule") for c in checks if not c.get("passed")],
                "execution_id": item.get("execution_id"),
                "status": item.get("status"),
            }
        )

    result = {
        "record_id": record_id,
        "anomaly_score": anomaly_score,
        "conclusion": conclusion,
        "consistency_checks": checks,
        "task_results": task_results,
        "evidence_chain": evidence_chain,
    }

    persist_evidence(record_id, evidence_chain)
    archive_stage_result(record_id, "cross_validate_result.json", result)
    return result
