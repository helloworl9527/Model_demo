import time
from typing import Any

from execution.celery_app import celery_app
from execution.event_bus import publish_event
from execution.state_store import set_status


@celery_app.task(name="execution.workers.run_specialist")
def run_specialist(execution_id: str, routed_task: dict[str, Any], parsed_context: dict[str, Any]):
    """模拟专业模型执行过程，并持续回写状态与事件。"""
    task_type = routed_task.get("task_type", "unknown")

    try:
        set_status(execution_id, "running", task_type)
        publish_event(execution_id, "running", {"task_type": task_type})

        # Simulate an intermediate stage and expose partial output for front-end polling.
        time.sleep(1)
        partial = {
            "task_type": task_type,
            "step": "initial_scan",
            "summary": "specialist model started and produced partial signals",
        }
        set_status(execution_id, "partial", task_type, partial)
        publish_event(execution_id, "partial", partial)

        time.sleep(1)
        result = {
            "task_type": task_type,
            "findings": [f"{task_type} completed"],
            "route_method": routed_task.get("route_method"),
            "confidence": routed_task.get("confidence"),
            "assigned_model": routed_task.get("assigned_model"),
            "assigned_tools": routed_task.get("assigned_tools", []),
            "context_keys": list(parsed_context.keys()) if parsed_context else [],
        }
        set_status(execution_id, "done", task_type, result)
        publish_event(execution_id, "done", result)
        return result

    except Exception as exc:
        error_payload = {"task_type": task_type, "error": str(exc)}
        set_status(execution_id, "error", task_type, error_payload)
        publish_event(execution_id, "error", error_payload)
        raise
