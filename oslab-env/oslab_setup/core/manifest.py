import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from oslab_setup.errors import ManifestError
from oslab_setup.core.log import logger, trace


@dataclass(frozen=True)
class Manifest:
    root: Path
    environment_version: str
    ubuntu_version: str
    architectures: tuple[str, ...]
    apt_mirror: dict[str, str]
    versions: dict[str, Any]
    packages: dict[str, tuple[str, ...]]

    def validate(self) -> None:
        if not self.environment_version:
            raise ManifestError("platform.toml 缺少 environment_version")
        if not self.ubuntu_version:
            raise ManifestError("platform.toml 缺少 ubuntu.version")
        if set(self.architectures) != {"amd64", "arm64"}:
            raise ManifestError("支持的架构必须且只能是 amd64 和 arm64")
        for key in ("name", "amd64_uri", "arm64_uri"):
            if not self.apt_mirror.get(key):
                raise ManifestError(f"platform.toml 缺少 apt_mirror.{key}")
        for group, packages in self.packages.items():
            if not packages or not all(isinstance(package, str) and package for package in packages):
                raise ManifestError(f"软件包组 {group} 为空或格式无效")
        for component, version_data in self.versions.items():
            if not isinstance(version_data, dict):
                raise ManifestError(f"版本项 {component} 必须是 TOML 表")

    def packages_for(self, group: str) -> tuple[str, ...]:
        try:
            return self.packages[group]
        except KeyError as error:
            raise ManifestError(f"未知软件包组：{group}") from error

def _read(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except FileNotFoundError as error:
        raise ManifestError(f"缺少必需的清单文件：{path}") from error
    except tomllib.TOMLDecodeError as error:
        raise ManifestError(f"TOML 格式无效：{path}：{error}") from error


def load_manifest(root: Path) -> Manifest:
    manifest_dir = root / "manifest"
    logger.debug("加载环境清单目录：%s", manifest_dir)
    platform = _read(manifest_dir / "platform.toml")
    versions = _read(manifest_dir / "versions.toml")
    packages_raw = _read(manifest_dir / "packages.toml")
    try:
        packages = {group: tuple(values["packages"]) for group, values in packages_raw.items()}
        result = Manifest(
            root=root,
            environment_version=platform["environment_version"],
            ubuntu_version=platform["ubuntu"]["version"],
            architectures=tuple(platform["supported"]["architectures"]),
            apt_mirror=platform["apt_mirror"],
            versions=versions,
            packages=packages,
        )
    except (KeyError, TypeError) as error:
        raise ManifestError(f"清单结构不符合预期：{error}") from error
    result.validate()
    logger.info("环境清单加载完成：版本=%s，支持架构=%s", result.environment_version, ", ".join(result.architectures))
    trace("已加载清单：软件包组=%s", ", ".join(result.packages))
    return result
