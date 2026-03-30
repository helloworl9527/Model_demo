from typing import Any

from pydantic import BaseModel, Field


class ExecuteRequest(BaseModel):
    """执行层请求：包含 record_id、任务清单与解析上下文。"""
    record_id: str | None = None
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    parsed_context: dict[str, Any] = Field(default_factory=dict)


class ExecuteResponse(BaseModel):
    """执行层响应：返回已提交作业列表。"""
    jobs: list[dict[str, str]] = Field(default_factory=list)
