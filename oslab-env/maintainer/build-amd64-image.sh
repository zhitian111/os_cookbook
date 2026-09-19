#!/usr/bin/env bash
set -euo pipefail

echo "此脚本只提供发布检查清单，不绑定具体虚拟机平台。"
echo "请在干净的 Ubuntu 26.04 amd64 客户机中完成："
echo "  1. 克隆带发布标签的 oslab-env 版本。"
echo "  2. 确认 bash ./setup.sh 与 bash ./verify.sh 均成功。"
echo "  3. 关闭客户机，并使用课程选定的虚拟机平台导出镜像。"
