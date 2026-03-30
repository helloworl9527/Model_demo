from typing import Any


def _safe_float(v: Any, default: float = 0.0) -> float:
    """安全转换为浮点数，失败时返回默认值。"""
    try:
        return float(v)
    except Exception:
        return default


def run_consistency_checks(parsed_context: dict[str, Any], task_results: list[dict[str, Any]]):
    """执行基础一致性规则，输出逐条规则检查结果。"""
    checks: list[dict[str, Any]] = []

    all_done = all((x.get("status") == "done") for x in task_results) if task_results else False
    checks.append(
        {
            "rule": "all_tasks_completed",
            "passed": all_done,
            "severity": "high",
            "message": "All sub tasks should reach done status before final audit conclusion.",
        }
    )

    has_contract = any(x.get("task_type") == "contract_tender_check" for x in task_results)
    checks.append(
        {
            "rule": "contract_task_covered",
            "passed": has_contract,
            "severity": "medium",
            "message": "Contract and tender checking should be covered in this audit pattern.",
        }
    )

    low_conf = [x for x in task_results if _safe_float(x.get("confidence")) < 0.3]
    checks.append(
        {
            "rule": "route_confidence_threshold",
            "passed": len(low_conf) == 0,
            "severity": "medium",
            "message": f"{len(low_conf)} tasks below confidence threshold 0.3",
        }
    )

    risk_level = (parsed_context or {}).get("risk_level", "medium")
    if risk_level == "high":
        checks.append(
            {
                "rule": "high_risk_minimum_coverage",
                "passed": len(task_results) >= 2,
                "severity": "high",
                "message": "High risk audits require at least 2 specialist tasks.",
            }
        )

    return checks


def calculate_anomaly_score(checks: list[dict[str, Any]]) -> float:
    """根据规则失败严重度计算异常分数（0-100）。"""
    score = 0.0
    for c in checks:
        if c.get("passed"):
            continue
        sev = c.get("severity")
        if sev == "high":
            score += 40
        elif sev == "medium":
            score += 20
        else:
            score += 10
    return min(score, 100.0)
