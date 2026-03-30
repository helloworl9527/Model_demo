import os
from pathlib import Path


# 以仓库根目录作为默认锚点，确保代码在任意服务器路径都能运行。
PROJECT_ROOT = Path(__file__).resolve().parent

# 解析记录目录：可通过 PARSE_STORAGE_DIR 覆盖。
RECORDS_DIR = Path(os.getenv("PARSE_STORAGE_DIR", str(PROJECT_ROOT / "data" / "records")))
# 任务画像文件：用于 embedding 路由。
KNOWLEDGE_PROFILES_PATH = Path(
    os.getenv(
        "TASK_PROFILES_PATH",
        str(PROJECT_ROOT / "data" / "knowledge" / "task_profiles.json"),
    )
)
# 证据链数据库目录：默认 SQLite 存在 data/evidence 下。
EVIDENCE_DB_DIR = Path(os.getenv("EVIDENCE_DB_DIR", str(PROJECT_ROOT / "data" / "evidence")))
