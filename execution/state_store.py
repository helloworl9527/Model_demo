import json
import os
import time
from typing import Any

import redis
from dotenv import load_dotenv

load_dotenv()

_redis = redis.Redis.from_url(
    os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"), decode_responses=True
)


def set_status(execution_id: str, status: str, task_type: str, payload: dict[str, Any] | None = None):
    """写入执行状态快照到 Redis Hash。"""
    key = f"audit:exec:{execution_id}"
    mapping = {
        "execution_id": execution_id,
        "task_type": task_type,
        "status": status,
        "updated_at": str(int(time.time())),
    }
    if payload is not None:
        mapping["payload"] = json.dumps(payload, ensure_ascii=False)
    _redis.hset(key, mapping=mapping)


def get_status(execution_id: str) -> dict[str, Any]:
    """读取并反序列化某个执行任务的状态。"""
    data = _redis.hgetall(f"audit:exec:{execution_id}")
    if not data:
        return {}
    payload = data.get("payload")
    if payload:
        try:
            data["payload"] = json.loads(payload)
        except json.JSONDecodeError:
            pass
    return data
