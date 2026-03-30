from typing import List, Literal
from pydantic import BaseModel, Field


class RoutedTask(BaseModel):
    """单个子任务的路由结果与执行配置。"""
    task_type: str
    priority: Literal["low", "medium", "high"] = "medium"
    route_method: Literal["rule", "embedding", "hybrid"] = "hybrid"
    confidence: float = 0.0
    assigned_model: str
    assigned_tools: List[str] = Field(default_factory=list)
    reason: str = ""


class DecomposeResult(BaseModel):
    """任务分解阶段的整体输出。"""
    tasks: List[RoutedTask] = Field(default_factory=list)