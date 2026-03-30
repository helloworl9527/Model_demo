import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI
from schema import StructuredAuditTask

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("缺少 DEEPSEEK_API_KEY，请在 .env 或环境变量中配置")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)

SYSTEM_PROMPT = """
你是审计方案信息抽取器。只输出 JSON，不要输出任何解释。
必须严格符合以下字段：
objective: string[]
scope: { org_units: string[], period: string|null, datasets: string[] }
focus_areas: string[]
time_requirements: string[]
audit_objects: string[]
risk_level: "low" | "medium" | "high"
"""

def _safe_json_loads(text: str) -> Dict[str, Any]:
    """兼容模型返回的 markdown 代码块并安全解析 JSON。"""
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        lines = t.splitlines()
        if lines and lines[0].lower().strip() in {"json", "javascript"}:
            lines = lines[1:]
        t = "\n".join(lines).strip()
    return json.loads(t)

def parse_audit_plan_to_structured_json(plan_text: str) -> StructuredAuditTask:
    """调用大模型完成审计方案语义抽取并校验为结构化模型。"""
    resp = client.chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"请从以下审计方案中抽取结构化信息：\n\n{plan_text}"},
        ],
        temperature=0,
    )

    raw = (resp.choices[0].message.content or "").strip()
    data = _safe_json_loads(raw)
    return StructuredAuditTask.model_validate(data)