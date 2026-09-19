#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "请使用 pip-tools 或 uv 等可锁定版本的解析器，从下列文件重新生成 requirements.lock："
echo "  $ROOT/requirements.in"
echo "提交前必须审阅全部直接和传递依赖的差异。"
