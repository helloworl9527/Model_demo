import os
from pathlib import Path

from schema import StructuredAuditTask
from routing.hybrid_router import route_hybrid
from settings import KNOWLEDGE_PROFILES_PATH


def decompose_and_route(parsed: StructuredAuditTask):
    """根据知识画像配置执行混合路由，产出可执行子任务。"""
    profiles_path = os.getenv("TASK_PROFILES_PATH", str(KNOWLEDGE_PROFILES_PATH))

    if not Path(profiles_path).exists():
        raise FileNotFoundError(f"task profiles not found: {profiles_path}")

    return route_hybrid(parsed, profiles_path)
