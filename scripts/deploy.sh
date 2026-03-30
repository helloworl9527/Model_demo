#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
LOG_DIR="$ROOT_DIR/logs"
PYTHON_BIN="${PYTHON_BIN:-python3}"
API_PORT="${API_PORT:-8000}"
WORKER_CONCURRENCY="${WORKER_CONCURRENCY:-2}"

mkdir -p "$LOG_DIR"
mkdir -p "$ROOT_DIR/data/records" "$ROOT_DIR/data/evidence"

install_redis_if_missing() {
  if command -v redis-server >/dev/null 2>&1; then
    return 0
  fi

  echo "[deploy] redis-server 未检测到，尝试自动安装..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y redis-server
  elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y redis
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y redis
  elif command -v brew >/dev/null 2>&1; then
    HOMEBREW_NO_AUTO_UPDATE=1 brew install redis
  else
    echo "[deploy] 未找到可用包管理器，请手动安装 Redis。"
    exit 1
  fi
}

start_redis() {
  if command -v redis-cli >/dev/null 2>&1 && redis-cli ping >/dev/null 2>&1; then
    echo "[deploy] Redis 已在运行"
    return 0
  fi

  if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl start redis || sudo systemctl start redis-server || true
  fi

  if command -v service >/dev/null 2>&1; then
    sudo service redis-server start || sudo service redis start || true
  fi

  if command -v redis-cli >/dev/null 2>&1 && redis-cli ping >/dev/null 2>&1; then
    echo "[deploy] Redis 启动成功"
    return 0
  fi

  echo "[deploy] 尝试以守护进程方式启动 Redis"
  redis-server --daemonize yes || true

  if ! (command -v redis-cli >/dev/null 2>&1 && redis-cli ping >/dev/null 2>&1); then
    echo "[deploy] Redis 启动失败，请手动检查。"
    exit 1
  fi
}

setup_python_env() {
  if [ ! -d "$VENV_DIR" ]; then
    echo "[deploy] 创建虚拟环境: $VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi

  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  pip install -U pip
  pip install -r "$ROOT_DIR/requirements.txt"
}

prepare_env_file() {
  if [ ! -f "$ROOT_DIR/.env" ]; then
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
    echo "[deploy] 已生成 .env，请填写 DEEPSEEK_API_KEY 后重新执行。"
    exit 1
  fi
}

start_services() {
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"

  echo "[deploy] 停止旧进程（如存在）"
  pkill -f "uvicorn main:app" || true
  pkill -f "celery -A execution.celery_app:celery_app worker" || true

  echo "[deploy] 启动 API"
  nohup uvicorn main:app --app-dir "$ROOT_DIR" --host 0.0.0.0 --port "$API_PORT" \
    > "$LOG_DIR/api.log" 2>&1 &

  echo "[deploy] 启动 Worker"
  nohup env PYTHONPATH="$ROOT_DIR" celery -A execution.celery_app:celery_app worker \
    -l info -Q audit_exec --concurrency="$WORKER_CONCURRENCY" -n "audit_worker@%h" \
    > "$LOG_DIR/worker.log" 2>&1 &

  sleep 2
  echo "[deploy] API:    http://0.0.0.0:$API_PORT/demo"
  echo "[deploy] 日志:   $LOG_DIR/api.log"
  echo "[deploy] 日志:   $LOG_DIR/worker.log"
}

main() {
  echo "[deploy] 项目目录: $ROOT_DIR"
  install_redis_if_missing
  start_redis
  setup_python_env
  prepare_env_file
  start_services
  echo "[deploy] 部署完成"
}

main "$@"
