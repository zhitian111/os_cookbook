#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$ROOT/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
    echo "OSLab 安装器虚拟环境不存在。请先运行 ./setup.sh。" >&2
    exit 1
fi

exec "$PYTHON" -m oslab_setup verify "$@"
