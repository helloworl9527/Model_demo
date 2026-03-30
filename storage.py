import json
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any

from settings import RECORDS_DIR


BASE_DIR = RECORDS_DIR

def _new_record_dir() -> Path:
    """创建新的记录目录，目录名由时间戳+短 UUID 构成。"""
    # 每次解析请求都隔离到独立目录，便于追溯同一条审计链路。
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    record_id = f"{ts}_{uuid4().hex[:8]}"
    record_dir = BASE_DIR / record_id
    record_dir.mkdir(parents=True, exist_ok=True)
    return record_dir


def save_text_submission(original_text: str, parsed_result: Dict[str, Any]) -> str:
    """保存文本输入与解析结果，返回本次 record_id。"""
    record_dir = _new_record_dir()

    (record_dir / "original.txt").write_text(original_text, encoding="utf-8")
    (record_dir / "parsed_result.json").write_text(
        json.dumps(parsed_result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (record_dir / "parsed_structed.json").write_text(
        json.dumps(parsed_result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return record_dir.name


def save_file_submission(
    filename: str, content: bytes, parsed_result: Dict[str, Any]
) -> str:
    """保存上传文件与解析结果，返回本次 record_id。"""
    record_dir = _new_record_dir()

    safe_name = Path(filename).name or "upload.bin"
    (record_dir / safe_name).write_bytes(content)
    (record_dir / "parsed_result.json").write_text(
        json.dumps(parsed_result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (record_dir / "parsed_structed.json").write_text(
        json.dumps(parsed_result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return record_dir.name


def _record_dir(record_id: str) -> Path:
    """根据 record_id 定位目录，不存在则抛出异常。"""
    record_dir = BASE_DIR / record_id
    if not record_dir.exists():
        raise FileNotFoundError(f"record not found: {record_id}")
    return record_dir


def archive_stage_result(record_id: str, file_name: str, payload: Dict[str, Any]) -> str:
    """通用归档函数：将任意阶段结果写入对应记录目录。"""
    record_dir = _record_dir(record_id)
    target = record_dir / file_name
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(target)


def archive_decompose_result(record_id: str, parsed_result: Dict[str, Any], decompose_result: Dict[str, Any]) -> str:
    """归档任务分解结果，输出为 decompose_result.json。"""
    payload = {
        "record_id": record_id,
        "parsed": parsed_result,
        "decompose": decompose_result,
    }
    return archive_stage_result(record_id, "decompose_result.json", payload)


def archive_execute_result(record_id: str, execute_request: Dict[str, Any], execute_response: Dict[str, Any]) -> str:
    """归档执行提交信息，输出为 execute_result.json。"""
    payload = {
        "record_id": record_id,
        "request": execute_request,
        "response": execute_response,
    }
    return archive_stage_result(record_id, "execute_result.json", payload)


def load_record_parsed_context(record_id: str) -> Dict[str, Any]:
    """按优先级读取某条记录的结构化解析上下文。"""
    record_dir = _record_dir(record_id)
    candidate_files = [
        record_dir / "parsed_structed.json",
        record_dir / "parsed_structured.json",
        record_dir / "parsed_result.json",
    ]

    for p in candidate_files:
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
            return data["data"]
        if isinstance(data, dict):
            return data

    raise FileNotFoundError(f"parsed context not found for record: {record_id}")