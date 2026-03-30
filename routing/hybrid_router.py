from typing import Dict, List
from schema import StructuredAuditTask
from routing.decompose_schema import RoutedTask, DecomposeResult
from routing.rule_router import route_by_rule
from routing.embedding_router import EmbeddingRouter
from routing.model_registry import REGISTRY


def route_hybrid(parsed: StructuredAuditTask, profiles_path: str) -> DecomposeResult:
    """融合规则路由与向量路由结果，输出最终任务分解清单。"""
    rule_hits = route_by_rule(parsed)
    emb_router = EmbeddingRouter(profiles_path)
    emb_hits = emb_router.route(parsed)

    all_types = set(rule_hits.keys()) | set(emb_hits.keys())
    tasks: List[RoutedTask] = []

    for task_type in all_types:
        r = rule_hits.get(task_type, 0.0)
        e = emb_hits.get(task_type, 0.0)
        conf = max(r, e) if (r == 0 or e == 0) else (0.6 * r + 0.4 * e)

        route_method = "hybrid"
        if r > 0 and e == 0:
            route_method = "rule"
        elif e > 0 and r == 0:
            route_method = "embedding"

        cfg = REGISTRY[task_type]
        priority = "high" if parsed.risk_level == "high" else "medium"

        tasks.append(
            RoutedTask(
                task_type=task_type,
                priority=priority,
                route_method=route_method,
                confidence=round(conf, 4),
                assigned_model=cfg["assigned_model"],
                assigned_tools=cfg["assigned_tools"],
                reason=f"rule={round(r,4)}, embedding={round(e,4)}"
            )
        )

    return DecomposeResult(tasks=sorted(tasks, key=lambda x: x.confidence, reverse=True))