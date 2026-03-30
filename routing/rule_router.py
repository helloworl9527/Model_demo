from typing import Dict, List
from schema import StructuredAuditTask

RULES = {
    "finance_review": ["财务", "收支", "报销", "凭证", "总账", "资金"],
    "contract_tender_check": ["合同", "招标", "投标", "采购", "评标", "履约"],
    "inventory_count": ["物资", "材料", "库存", "盘点", "出入库", "账实"],
    "rd_decision_eval": ["科研", "立项", "决策", "论证", "纪要", "评审"]
}

def _build_text(parsed: StructuredAuditTask) -> str:
    """将结构化字段拼接为规则匹配文本。"""
    chunks = []
    chunks.extend(parsed.objective)
    chunks.extend(parsed.focus_areas)
    chunks.extend(parsed.audit_objects)
    chunks.extend(parsed.scope.org_units)
    chunks.extend(parsed.scope.datasets)
    if parsed.scope.period:
        chunks.append(parsed.scope.period)
    return " ".join(chunks)

def route_by_rule(parsed: StructuredAuditTask) -> Dict[str, float]:
    """基于关键词命中次数计算规则路由置信度。"""
    text = _build_text(parsed)
    hit: Dict[str, float] = {}
    for task_type, keywords in RULES.items():
        count = sum(1 for k in keywords if k in text)
        if count > 0:
            hit[task_type] = min(1.0, 0.4 + 0.15 * count)
    return hit