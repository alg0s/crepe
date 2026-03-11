#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"
VENV_UVICORN="$ROOT_DIR/.venv/bin/uvicorn"
PID_FILE=""

usage() {
  cat <<'USAGE'
Usage:
  ./run-crepe.sh run [pipeline] [extra args]
  ./run-crepe.sh web
  ./run-crepe.sh stop
  ./run-crepe.sh status [--limit N]
  ./run-crepe.sh pause [run_id]
  ./run-crepe.sh cancel [run_id]
  ./run-crepe.sh resume [run_id]

Modes:
  run                Run backend pipeline command in the terminal
  web                Start backend API + frontend UI together
  stop               Stop tracked crepe web services
  status             Show web service status and recent run status
  pause              Pause the active running job
  cancel             Cancel the active job
  resume             Clear pause state for a run

Pipelines for run:
  all (default), extract, normalize, analyze, suggest, demo

Examples:
  ./run-crepe.sh run all
  ./run-crepe.sh run demo --run-id demo-run
  ./run-crepe.sh web
  ./run-crepe.sh stop
  ./run-crepe.sh status --limit 5
  ./run-crepe.sh pause
  ./run-crepe.sh cancel
USAGE
}

load_env_file() {
  if [[ -f "$ROOT_DIR/.env" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "$ROOT_DIR/.env"
    set +a
  fi
}

ensure_default_runtime_paths() {
  if [[ -z "${CREPE_CONFIG_DIR:-}" ]]; then
    CREPE_CONFIG_DIR="$HOME/.config/crepe"
    export CREPE_CONFIG_DIR
  fi
  if [[ -z "${CREPE_BASE_DIR:-}" ]]; then
    CREPE_BASE_DIR="$CREPE_CONFIG_DIR/data"
    export CREPE_BASE_DIR
  fi
  if [[ -z "${CREPE_DB_PATH:-}" ]]; then
    CREPE_DB_PATH="$CREPE_BASE_DIR/crepe.sqlite3"
    export CREPE_DB_PATH
  fi
  mkdir -p "$CREPE_BASE_DIR"
  PID_FILE="$CREPE_CONFIG_DIR/web.pids.json"
}

require_graph_credentials() {
  if ! (cd "$BACKEND_DIR" && PYTHONPATH=. "$VENV_PYTHON" -c "from crepe.config import load_config, validate_credentials; validate_credentials(load_config())" >/dev/null 2>&1); then
    echo "Missing required Graph credentials." >&2
    echo "Open the Setup page and save credentials, or set MS_TENANT_ID/MS_CLIENT_ID/MS_CLIENT_SECRET." >&2
    exit 1
  fi
}

require_no_active_job() {
  if ! (cd "$BACKEND_DIR" && PYTHONPATH=. "$VENV_PYTHON" - <<'PY'
from crepe.config import load_config
from crepe.storage.db import RunDatabase

cfg = load_config()
db = RunDatabase(cfg.db_path)
active = db.latest_run_by_status(("running", "paused"))
if active is not None:
    raise SystemExit(1)
raise SystemExit(0)
PY
  ); then
    echo "Another job is active (running or paused). Use 'crepe status', then pause/cancel/resume as needed." >&2
    exit 1
  fi
}

require_runtime() {
  if [[ ! -x "$VENV_PYTHON" ]]; then
    echo "Python runtime not found at $VENV_PYTHON" >&2
    echo "Create the venv and install requirements first." >&2
    exit 1
  fi
}

is_pid_running() {
  local pid="$1"
  if [[ -z "$pid" ]]; then
    return 1
  fi
  kill -0 "$pid" 2>/dev/null
}

write_pid_file() {
  local backend_pid="$1"
  local frontend_pid="$2"
  mkdir -p "$(dirname "$PID_FILE")"
  "$VENV_PYTHON" - "$PID_FILE" "$backend_pid" "$frontend_pid" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

path = Path(sys.argv[1])
backend_pid = int(sys.argv[2])
frontend_pid = int(sys.argv[3])
payload = {
    "backend_pid": backend_pid,
    "frontend_pid": frontend_pid,
    "started_at": datetime.now(tz=timezone.utc).isoformat(),
}
path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY
}

read_pid_field() {
  local field="$1"
  if [[ ! -f "$PID_FILE" ]]; then
    return 0
  fi
  "$VENV_PYTHON" - "$PID_FILE" "$field" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
field = sys.argv[2]
if not path.exists():
    raise SystemExit(0)
payload = json.loads(path.read_text(encoding="utf-8"))
value = payload.get(field)
if value is None:
    raise SystemExit(0)
print(value)
PY
}

stop_tracked_services() {
  local backend_pid frontend_pid
  backend_pid="$(read_pid_field backend_pid || true)"
  frontend_pid="$(read_pid_field frontend_pid || true)"

  local stopped_any=0
  for pid in "$backend_pid" "$frontend_pid"; do
    if [[ -n "$pid" ]] && is_pid_running "$pid"; then
      kill "$pid" 2>/dev/null || true
      stopped_any=1
    fi
  done

  if [[ $stopped_any -eq 1 ]]; then
    sleep 1
    for pid in "$backend_pid" "$frontend_pid"; do
      if [[ -n "$pid" ]] && is_pid_running "$pid"; then
        kill -9 "$pid" 2>/dev/null || true
      fi
    done
  fi

  rm -f "$PID_FILE"
}

show_service_status() {
  local backend_pid frontend_pid
  backend_pid="$(read_pid_field backend_pid || true)"
  frontend_pid="$(read_pid_field frontend_pid || true)"

  echo "Service status:"
  if [[ -z "$backend_pid" && -z "$frontend_pid" ]]; then
    echo "- web: not tracked"
    return
  fi

  if [[ -n "$backend_pid" ]]; then
    if is_pid_running "$backend_pid"; then
      echo "- backend: running (pid=$backend_pid)"
    else
      echo "- backend: stopped (stale pid=$backend_pid)"
    fi
  fi

  if [[ -n "$frontend_pid" ]]; then
    if is_pid_running "$frontend_pid"; then
      echo "- frontend: running (pid=$frontend_pid)"
    else
      echo "- frontend: stopped (stale pid=$frontend_pid)"
    fi
  fi
}

mode="${1:-}"
if [[ -z "$mode" ]]; then
  usage
  exit 1
fi
shift || true

load_env_file
ensure_default_runtime_paths
require_runtime

case "$mode" in
  run|cli)
    pipeline="all"
    if [[ $# -gt 0 && "${1:0:1}" != "-" ]]; then
      pipeline="$1"
      shift
    fi
    case "$pipeline" in
      all|extract|normalize|analyze|suggest|demo) ;;
      *)
        echo "Unknown pipeline: $pipeline" >&2
        usage
        exit 1
        ;;
    esac
    if [[ "$pipeline" == "all" || "$pipeline" == "extract" ]]; then
      require_graph_credentials
    fi
    require_no_active_job
    cd "$BACKEND_DIR"
    PYTHONPATH=. "$VENV_PYTHON" -m crepe.cli "$pipeline" "$@"
    ;;

  web)
    if [[ ! -x "$VENV_UVICORN" ]]; then
      echo "uvicorn not found at $VENV_UVICORN" >&2
      echo "Install backend dependencies first." >&2
      exit 1
    fi
    if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
      echo "Missing frontend dependencies at $FRONTEND_DIR/node_modules" >&2
      echo "Run: cd $FRONTEND_DIR && npm install" >&2
      exit 1
    fi

    cleanup() {
      if [[ -n "${BACKEND_PID:-}" ]]; then
        kill "$BACKEND_PID" 2>/dev/null || true
      fi
      if [[ -n "${FRONTEND_PID:-}" ]]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
      fi
      rm -f "$PID_FILE"
    }
    trap cleanup EXIT INT TERM

    if [[ -f "$PID_FILE" ]]; then
      echo "Found existing web pid file at $PID_FILE; attempting to stop stale services first."
      stop_tracked_services
    fi

    (
      cd "$BACKEND_DIR"
      PYTHONPATH=. "$VENV_UVICORN" crepe.api.app:create_app --factory --host 127.0.0.1 --port 8000
    ) &
    BACKEND_PID=$!

    (
      cd "$FRONTEND_DIR"
      npm run dev -- --host 127.0.0.1 --port 5173
    ) &
    FRONTEND_PID=$!

    write_pid_file "$BACKEND_PID" "$FRONTEND_PID"

    echo "Backend API:   http://127.0.0.1:8000"
    echo "Frontend UI:   http://127.0.0.1:5173"
    echo "PID file:      $PID_FILE"
    echo "Press Ctrl+C to stop both services."

    wait "$BACKEND_PID" "$FRONTEND_PID"
    ;;

  stop|kill)
    stop_tracked_services
    echo "Stopped tracked crepe web services."
    ;;

  status)
    limit="10"
    if [[ $# -ge 2 && "$1" == "--limit" ]]; then
      limit="$2"
    fi
    show_service_status
    echo
    cd "$BACKEND_DIR"
    PYTHONPATH=. "$VENV_PYTHON" -m crepe.control_cli status --limit "$limit"
    ;;

  pause)
    cd "$BACKEND_DIR"
    if [[ $# -ge 1 ]]; then
      PYTHONPATH=. "$VENV_PYTHON" -m crepe.control_cli pause --run-id "$1"
    else
      PYTHONPATH=. "$VENV_PYTHON" -m crepe.control_cli pause
    fi
    ;;

  cancel)
    cd "$BACKEND_DIR"
    if [[ $# -ge 1 ]]; then
      PYTHONPATH=. "$VENV_PYTHON" -m crepe.control_cli cancel --run-id "$1"
    else
      PYTHONPATH=. "$VENV_PYTHON" -m crepe.control_cli cancel
    fi
    ;;

  resume)
    cd "$BACKEND_DIR"
    if [[ $# -ge 1 ]]; then
      PYTHONPATH=. "$VENV_PYTHON" -m crepe.control_cli resume --run-id "$1"
    else
      PYTHONPATH=. "$VENV_PYTHON" -m crepe.control_cli resume
    fi
    ;;

  *)
    echo "Unknown mode: $mode" >&2
    usage
    exit 1
    ;;
esac
