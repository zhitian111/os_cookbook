#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/.venv"
cd "$ROOT"

restore_apt_mirror() {
    python3 -m oslab_setup --no-color apt-mirror restore || \
        echo "警告：未能自动恢复 APT 源。请重新运行 ./setup.sh，或联系课程助教并附上日志。" >&2
}

if [[ "$(id -u)" -eq 0 ]]; then
    echo "请以普通用户运行 ./setup.sh；安装器仅在需要时请求 sudo。" >&2
    exit 1
fi

if ! command -v sudo >/dev/null 2>&1 || ! command -v apt-get >/dev/null 2>&1 || ! command -v python3 >/dev/null 2>&1; then
    echo "基础条件不满足：OSLab 安装器需要 sudo、apt-get 和 python3。" >&2
    exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "Python 版本过低：OSLab 安装器需要 Python 3.11 或更高版本。" >&2
    exit 1
fi

python3 -m oslab_setup --no-color bootstrap-check

if ! sudo -v; then
    echo "sudo 验证失败：当前普通用户必须具有 sudo 权限。" >&2
    exit 1
fi

trap restore_apt_mirror EXIT
python3 -m oslab_setup apt-mirror enable
if ! sudo apt-get update; then
    echo "APT 索引更新失败。请检查网络、DNS、代理、阿里云镜像可达性或证书配置后重试。" >&2
    exit 1
fi
if ! sudo apt-get install -y python3 python3-venv ca-certificates curl; then
    echo "Bootstrap 基础软件包安装失败。请查看上方 APT 输出，并检查网络、镜像、磁盘空间及软件包冲突。" >&2
    exit 1
fi

if [[ ! -x "$VENV/bin/python" ]]; then
    if ! python3 -m venv "$VENV"; then
        echo "Python 虚拟环境创建失败。请确认 python3-venv 已正确安装、仓库目录可写且磁盘空间充足。" >&2
        exit 1
    fi
fi

if ! "$VENV/bin/python" -m pip install -r "$ROOT/requirements.lock"; then
    echo "Python 安装器依赖安装失败。请检查 PyPI、代理、DNS 和证书配置后重试。" >&2
    exit 1
fi
"$VENV/bin/python" -m oslab_setup install "$@"
