from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

from extractor import load_plan_text, load_plan_from_upload
from execution.event_bus import read_events
from execution.schemas import ExecuteRequest, ExecuteResponse
from execution.state_store import get_status
from llm_parser import parse_audit_plan_to_structured_json
from evidence.schemas import CrossValidateRequest, CrossValidateResponse
from schema import StructuredAuditTask
from services.cross_validate_service import cross_validate
from services.decompose_service import decompose_and_route
from services.execution_service import submit_execution
from storage import (
    archive_decompose_result,
    archive_execute_result,
    save_text_submission,
    save_file_submission,
)


app = FastAPI(title="Audit Semantic Parser")
DEMO_HTML_PATH = Path(__file__).parent / "frontend" / "index.html"


@app.get("/demo", include_in_schema=False)
def demo_page():
    """返回前端 Demo 页面，便于手工演示全流程。"""
    if not DEMO_HTML_PATH.exists():
        raise HTTPException(status_code=404, detail="demo page not found")
    return FileResponse(DEMO_HTML_PATH)


class ParseRequest(BaseModel):
    """解析请求体：支持纯文本或本地 PDF 路径。"""
    text: str | None = None
    pdf_path: str | None = None


@app.post("/decompose")
def decompose(
    parsed: StructuredAuditTask,
    record_id: str | None = None,
):
    """将结构化审计语义结果分解为子任务并返回路由结果。"""
    try:
        result = decompose_and_route(parsed)
        output = result.model_dump()
        if record_id:
            archive_decompose_result(record_id, parsed.model_dump(), output)
        return output
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/execute", response_model=ExecuteResponse)
def execute(req: ExecuteRequest):
    """提交子任务到异步执行层，并可选归档执行请求/响应。"""
    try:
        jobs = submit_execution(req.tasks, req.parsed_context)
        output = {"jobs": jobs}
        if req.record_id:
            archive_execute_result(req.record_id, req.model_dump(), output)
        return output
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/cross-validate", response_model=CrossValidateResponse)
def cross_validate_endpoint(req: CrossValidateRequest):
    """汇总执行结果并生成交叉验证结论与证据链。"""
    try:
        return cross_validate(
            record_id=req.record_id,
            execution_ids=req.execution_ids,
            parsed_context=req.parsed_context,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/executions/{execution_id}")
def execution_status(execution_id: str):
    """查询单个执行任务的最新状态快照。"""
    try:
        data = get_status(execution_id)
        if not data:
            raise HTTPException(status_code=404, detail="execution not found")
        return data
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/executions/{execution_id}/events")
def execution_events(execution_id: str, count: int = 50):
    """读取单个执行任务的事件流，用于前端进度展示。"""
    try:
        return {"events": read_events(execution_id, count)}
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/parse")
def parse(req: ParseRequest):
    """解析文本或本地 PDF 输入，返回结构化结果并落盘。"""
    try:
        plan_text = load_plan_text(text=req.text, pdf_path=req.pdf_path)
        result = parse_audit_plan_to_structured_json(plan_text)
        result_dict = result.model_dump()

        if req.text and req.text.strip():
            record_id = save_text_submission(plan_text, result_dict)
        elif req.pdf_path and req.pdf_path.strip():
            src = Path(req.pdf_path.strip())
            record_id = save_file_submission(src.name, src.read_bytes(), result_dict)
        else:
            record_id = save_text_submission(plan_text, result_dict)

        return {"record_id": record_id, "data": result_dict}

    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/parse-file")
async def parse_file(file: UploadFile = File(...)):
    """解析上传文件（PDF/DOCX），返回结构化结果并落盘。"""
    try:
        content = await file.read()
        plan_text = load_plan_from_upload(file.filename or "", content)
        result = parse_audit_plan_to_structured_json(plan_text)
        result_dict = result.model_dump()

        record_id = save_file_submission(file.filename or "upload.bin", content, result_dict)
        return {"record_id": record_id, "data": result_dict}

    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
