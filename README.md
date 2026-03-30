# teacher_task_model

审计任务自动化 Demo：语义解析 -> 任务分解与路由 -> 并行执行 -> 交叉验证与证据链。

## 1. 技术方案概览
- 后端框架：FastAPI
- 语义解析：DeepSeek（OpenAI 兼容接口）
- 路由策略：规则路由 + Embedding 相似度路由（TF-IDF）
- 并行执行：Celery + Redis
- 状态与事件：Redis Hash + Redis Stream
- 证据链存储：SQLite（本地 Demo），可替换 Neo4j
- 可视化：`/demo` 单页前端

核心目标是让每次审计文档形成一个独立 `record_id`，并在同目录下持续归档阶段产物，保证可追溯。

## 2. 目录结构设计
```text
teacher_task_model/
├── main.py                      # API 入口（/parse /decompose /execute /cross-validate /demo）
├── settings.py                  # 统一路径/配置，避免绝对路径硬编码
├── extractor.py                 # 文本/PDF/DOCX 内容提取
├── llm_parser.py                # 审计语义解析
├── schema.py                    # 语义解析结构化模型
├── storage.py                   # record 归档与读取
├── routing/                     # 任务分解与路由
│   ├── rule_router.py
│   ├── embedding_router.py
│   ├── hybrid_router.py
│   ├── model_registry.py
│   └── decompose_schema.py
├── execution/                   # 并行执行层
│   ├── celery_app.py
│   ├── state_store.py
│   ├── event_bus.py
│   ├── schemas.py
│   └── workers/specialists.py
├── evidence/                    # 交叉验证与证据链
│   ├── rule_engine.py
│   ├── graph_store.py
│   └── schemas.py
├── services/                    # 服务编排层
│   ├── decompose_service.py
│   ├── execution_service.py
│   └── cross_validate_service.py
├── frontend/index.html          # Demo 可视化页面
├── data/
│   ├── knowledge/task_profiles.json
│   ├── records/                 # 每次任务归档目录
│   └── evidence/evidence.db
├── requirements.txt
├── .env.example
└── .gitignore
```

## 3. 部署指南（服务器/本地通用）
### 3.0 一键部署（推荐）
```bash
cd teacher_task_model
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

脚本会自动完成：Redis 检查/安装、Python 虚拟环境创建、依赖安装、API 与 Worker 启动。

### 3.1 克隆与环境
```bash
git clone <your_repo_url>
cd teacher_task_model
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`：填入 `DEEPSEEK_API_KEY`。

### 3.2 启动 Redis
```bash
redis-server
# 或系统服务方式启动 redis
```

### 3.3 启动 API
```bash
uvicorn main:app --reload --port 8000
```

### 3.4 启动 Worker（新终端）
```bash
PYTHONPATH=$(pwd) celery -A execution.celery_app:celery_app worker -l info -Q audit_exec --concurrency=2 -n audit_worker@%h
```

### 3.5 打开前端 Demo
浏览器访问：`http://127.0.0.1:8000/demo`

## 4. API 流程（无前端时）
1. `POST /parse` 或 `POST /parse-file` -> 获取 `record_id`
2. `POST /decompose?record_id=...` -> 输出 `tasks[]`
3. `POST /execute`（请求体携带 `record_id`）-> 提交异步执行
4. `GET /executions/{execution_id}` + `/events` -> 跟踪进度
5. `POST /cross-validate` -> 输出结论与证据链

## 5. 归档规则
每个 `record_id` 目录下通常包含：
- `parsed_result.json`
- `decompose_result.json`
- `execute_result.json`
- `cross_validate_result.json`
- 执行状态与事件快照文件（可选）

## 6. 关键设计原则
- 不依赖机器绝对路径：所有默认路径从 `settings.py` 的项目根目录派生。
- 环境可覆盖：通过 `.env` 覆盖存储目录和知识库路径。
- 各层职责单一：路由只负责分配，执行层只负责异步任务，证据层只负责校验和链路留痕。
- Demo 优先：当前规则偏流程校验，便于快速演示，后续可增强业务规则。

## 7. 常见问题
### Q1: Worker 启动报 `No module named 'execution'`
请在项目根目录启动，或设置：
```bash
PYTHONPATH=$(pwd)
```

### Q2: 一直停在 `queued`
通常是 Worker 未启动、队列名不一致，或任务未被 Celery 注册。

### Q3: 为什么很多结果是“通过”
当前 `rule_engine.py` 主要做流程一致性检查（done/coverage/confidence），不是深度业务审计打分。

## 8. 上 GitHub 前必须做的安全检查
- 不要提交 `.env`（`.gitignore` 已忽略）
- 若 API Key 曾进入 git 历史，请立即在平台侧轮换新 key
- 检查 `data/records/` 是否包含敏感业务文档，默认不提交
