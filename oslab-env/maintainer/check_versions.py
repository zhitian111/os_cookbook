#!/usr/bin/env python3
"""检查 lock 文件是否与 APT 包和 Rust 工具链配置一致。"""

import tomllib
from pathlib import Path


def load(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    versions = load(root / "manifest" / "versions.toml")
    package_groups = load(root / "manifest" / "packages.toml")
    expected = {
        "qemu_package": versions["qemu"]["apt_package"],
        "riscv_gnu_gcc_package": versions["riscv_gnu"]["gcc_package"],
        "riscv_gnu_binutils_package": versions["riscv_gnu"]["binutils_package"],
        "rust_toolchain": versions["rust"]["toolchain"],
    }
    failures = 0
    for architecture in ("amd64", "arm64"):
        lock = load(root / "lock" / f"{architecture}.lock.toml")
        if lock.get("status") != "tested":
            print(f"跳过 {architecture}：lock 尚未完成双架构实机验证")
            continue
        actual = lock.get("packages", {})
        required_packages = {
            package
            for group in package_groups.values()
            for package in group["packages"]
        }
        locked_versions = set(lock.get("apt_versions", {}))
        if actual != expected:
            failures += 1
            print(f"失败 {architecture}：lock 的关键工具契约与清单不一致")
        elif locked_versions != required_packages:
            failures += 1
            missing = sorted(required_packages - locked_versions)
            extra = sorted(locked_versions - required_packages)
            print(f"失败 {architecture}：APT 版本列表不完整；缺少={missing} 多余={extra}")
        else:
            print(f"通过 {architecture}")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
