import platform as host_platform
from dataclasses import dataclass
from pathlib import Path

from oslab_setup.errors import OslabError
from oslab_setup.core.log import logger


ARCHITECTURES = {"x86_64": "amd64", "aarch64": "arm64"}


@dataclass(frozen=True)
class Platform:
    id: str
    version: str
    architecture: str


def _os_release() -> dict[str, str]:
    path = Path("/etc/os-release")
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"')
    return values


def detect_platform() -> Platform:
    os_release = _os_release()
    raw_arch = host_platform.machine().lower()
    architecture = ARCHITECTURES.get(raw_arch, raw_arch)
    result = Platform(
        id=os_release.get("ID", host_platform.system().lower()),
        version=os_release.get("VERSION_ID", ""),
        architecture=architecture,
    )
    logger.debug("平台检测结果：系统=%s，版本=%s，架构=%s", result.id, result.version or "未知", result.architecture)
    return result


def require_supported(platform: Platform, ubuntu_version: str, architectures: tuple[str, ...]) -> None:
    if platform.id != "ubuntu":
        raise OslabError(f"不支持的操作系统：{platform.id}；需要 Ubuntu {ubuntu_version}")
    if platform.version != ubuntu_version:
        raise OslabError(f"不支持的 Ubuntu 版本：{platform.version or '未知'}；需要 Ubuntu {ubuntu_version}")
    if platform.architecture not in architectures:
        supported = ", ".join(architectures)
        raise OslabError(f"不支持的宿主架构：{platform.architecture}；支持的架构：{supported}")
