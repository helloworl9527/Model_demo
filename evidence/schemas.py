from typing import Any

from pydantic import BaseModel, Field


class CrossValidateRequest(BaseModel):
    """交叉验证请求：指定 record_id 及待验证执行任务。"""
    record_id: str
    execution_ids: list[str] = Field(default_factory=list)
    parsed_context: dict[str, Any] | None = None


class CrossValidateResponse(BaseModel):
    """交叉验证响应：返回评分、结论、检查项与证据链。"""
    record_id: str
    anomaly_score: float
    conclusion: str
    consistency_checks: list[dict[str, Any]] = Field(default_factory=list)
    task_results: list[dict[str, Any]] = Field(default_factory=list)
    evidence_chain: list[dict[str, Any]] = Field(default_factory=list)
