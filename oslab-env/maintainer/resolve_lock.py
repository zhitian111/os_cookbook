#!/usr/bin/env python3
"""在已验证的 Ubuntu 主机上记录本次 APT 实际解析到的版本。"""

import argparse
import subprocess
import tomllib
from pathlib import Path


def load(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def apt_version(package: str) -> str:
    completed = subprocess.run(["dpkg-query", "-W", package], text=True, capture_output=True, check=False)
    if completed.returncode:
        raise SystemExit(f"未安装必需 APT 包，无法生成 lock：{package}")
    fields = completed.stdout.strip().split()
    if len(fields) < 2:
        raise SystemExit(f"无法读取 APT 包版本：{package}")
    return fields[1]


def quote(value: str) -> str:
    return '"' + value.replace('"', '\\"') + '"'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arch", choices=("amd64", "arm64"), required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    platform = load(root / "manifest" / "platform.toml")
    versions = load(root / "manifest" / "versions.toml")
    packages = load(root / "manifest" / "packages.toml")
    required = tuple(
        dict.fromkeys(
            package
            for group in packages.values()
            for package in group["packages"]
        )
    )
    lines = [
        f"environment_version = {quote(platform['environment_version'])}",
        f"architecture = {quote(args.arch)}",
        'status = "tested"',
        "",
        "[packages]",
        f"qemu_package = {quote(versions['qemu']['apt_package'])}",
        f"riscv_gnu_gcc_package = {quote(versions['riscv_gnu']['gcc_package'])}",
        f"riscv_gnu_binutils_package = {quote(versions['riscv_gnu']['binutils_package'])}",
        f"rust_toolchain = {quote(versions['rust']['toolchain'])}",
        "",
        "[apt_versions]",
    ]
    for package in required:
        lines.append(f"{quote(package)} = {quote(apt_version(package))}")
    destination = root / "lock" / f"{args.arch}.lock.toml"
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已写入 {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
