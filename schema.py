# from pydantic import BaseModel, Field
# from typing import List, Optional, Literal


# class AuditScope(BaseModel):
#     org_units: List[str] = Field(default_factory=list, description="涉及部门/单位")
#     period: Optional[str] = Field(default=None, description="审计时间范围，如 2025-01~2025-12")
#     datasets: List[str] = Field(default_factory=list, description="涉及的数据来源")


# class StructuredAuditTask(BaseModel):
#     objective: List[str] = Field(default_factory=list, description="审计目标")
#     scope: AuditScope = Field(default_factory=AuditScope, description="审计范围")
#     focus_areas: List[str] = Field(default_factory=list, description="重点关注领域")
#     time_requirements: List[str] = Field(default_factory=list, description="时间要求/节点")
#     audit_objects: List[str] = Field(default_factory=list, description="审计对象")
#     risk_level: Literal["low", "medium", "high"] = "medium"


from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class AuditScope(BaseModel):
    """审计范围：组织、时间区间、数据来源。"""
    org_units: List[str] = Field(default_factory=list)
    period: Optional[str] = None
    datasets: List[str] = Field(default_factory=list)


class StructuredAuditTask(BaseModel):
    """语义解析层输出的统一结构化任务模型。"""
    objective: List[str] = Field(default_factory=list)
    scope: AuditScope = Field(default_factory=AuditScope)
    focus_areas: List[str] = Field(default_factory=list)
    time_requirements: List[str] = Field(default_factory=list)
    audit_objects: List[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high"] = "medium"