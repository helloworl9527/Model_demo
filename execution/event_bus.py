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


def publish_event(execution_id: str, event_type: str, body: dict[str, Any]):
    """发布执行事件到 Redis Stream，供前端轮询展示。"""
    stream = f"audit:events:{execution_id}"
    _redis.xadd(
        stream,
        {
            "event_type": event_type,
            "ts": str(int(time.time())),
            "body": json.dumps(body, ensure_ascii=False),
        },
    )


def read_events(execution_id: str, count: int = 50):
    """读取最近事件并解析事件体 JSON。"""
    stream = f"audit:events:{execution_id}"
    rows = _redis.xrevrange(stream, count=count)
    events = []
    for event_id, fields in rows:
        body = fields.get("body")
        if body:
            try:
                fields["body"] = json.loads(body)
            except json.JSONDecodeError:
                pass
        events.append({"id": event_id, **fields})
    return events
