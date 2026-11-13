#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
atlas_python=${PYTHON:-python}
export ATLAS_DATA="${ATLAS_DATA:-$PWD/.data}"
export PYTHONUNBUFFERED=1
export NO_PROXY=127.0.0.1,localhost
export no_proxy="$NO_PROXY"
export PYTHON="$atlas_python"
unset DATABASE_URL KAFKA_BOOTSTRAP
sh scripts/initialize.sh
pids=()
start() {
  "$atlas_python" -m "$@" &
  pids+=("$!")
}
cleanup() {
  if (("${#pids[@]}")); then
    kill "${pids[@]}" 2>/dev/null || true
    wait "${pids[@]}" 2>/dev/null || true
  fi
}
trap cleanup EXIT
trap 'exit 130' INT TERM
start uvicorn services.trips:app --host 127.0.0.1 --port 8001
start uvicorn services.dispatch:app --host 127.0.0.1 --port 8002
start uvicorn ml.serve:app --host 127.0.0.1 --port 8003
for attempt in {1..50}; do
  if "$atlas_python" -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8003/healthz', timeout=3).read()" 2>/dev/null; then
    break
  fi
  if [[ "$attempt" == 50 ]]; then
    echo 'Model server did not become ready' >&2
    exit 1
  fi
  sleep .4
done
start workers.events
start ml.rl watch --seconds 60
start uvicorn services.gateway:app --host 127.0.0.1 --port 8000
wait -n "${pids[@]}"
