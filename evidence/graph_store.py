import json
import sqlite3
from pathlib import Path
from time import time
from typing import Any

from settings import EVIDENCE_DB_DIR


def _db_path() -> Path:
    """返回证据库路径，不存在时自动创建目录。"""
    base = EVIDENCE_DB_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base / "evidence.db"


def _conn() -> sqlite3.Connection:
    """获取数据库连接并确保证据节点/边表已创建。"""
    conn = sqlite3.connect(_db_path())
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence_nodes (
            id TEXT PRIMARY KEY,
            node_type TEXT NOT NULL,
            label TEXT NOT NULL,
            attrs_json TEXT,
            created_at INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            src TEXT NOT NULL,
            dst TEXT NOT NULL,
            relation TEXT NOT NULL,
            attrs_json TEXT,
            created_at INTEGER NOT NULL
        )
        """
    )
    return conn


def persist_evidence(record_id: str, evidence_chain: list[dict[str, Any]]):
    """将证据链写入图结构表，形成 record -> evidence 关系。"""
    conn = _conn()
    now = int(time())
    root_id = f"record:{record_id}"
    conn.execute(
        "INSERT OR REPLACE INTO evidence_nodes(id, node_type, label, attrs_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (root_id, "record", record_id, "{}", now),
    )

    for idx, item in enumerate(evidence_chain, start=1):
        node_id = f"record:{record_id}:ev:{idx}"
        conn.execute(
            "INSERT OR REPLACE INTO evidence_nodes(id, node_type, label, attrs_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                node_id,
                "evidence",
                item.get("task_type", f"evidence-{idx}"),
                json.dumps(item, ensure_ascii=False),
                now,
            ),
        )
        conn.execute(
            "INSERT INTO evidence_edges(src, dst, relation, attrs_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (root_id, node_id, "supports", "{}", now),
        )

    conn.commit()
    conn.close()
