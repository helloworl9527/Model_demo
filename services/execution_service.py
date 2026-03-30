from uuid import uuid4

from execution.event_bus import publish_event
from execution.state_store import set_status
from execution.workers.specialists import run_specialist


def submit_execution(tasks: list[dict], parsed_context: dict):
    """将路由后的子任务批量提交到 Celery，并初始化状态与事件。"""
    jobs: list[dict[str, str]] = []

    for task in tasks:
        execution_id = uuid4().hex
        task_type = task.get("task_type", "unknown")

        set_status(
            execution_id,
            "queued",
            task_type,
            {
                "assigned_model": task.get("assigned_model"),
                "assigned_tools": task.get("assigned_tools", []),
            },
        )
        publish_event(execution_id, "queued", {"task_type": task_type})

        run_specialist.delay(execution_id, task, parsed_context)
        jobs.append({"execution_id": execution_id, "task_type": task_type})

    return jobs
