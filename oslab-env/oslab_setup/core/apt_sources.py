"""在一次安装会话内临时切换并可靠恢复 Ubuntu 官方 APT 源。"""

import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from oslab_setup.context import InstallContext
from oslab_setup.core.command import run
from oslab_setup.core.log import logger
from oslab_setup.errors import OslabError


_MANAGED_FILES = (
    Path("/etc/apt/sources.list"),
    Path("/etc/apt/sources.list.d/ubuntu.sources"),
)
_BACKUP_DIRNAME = "apt-sources-backup"
_OFFICIAL_UBUNTU_HOSTS = (
    "archive.ubuntu.com",
    "security.ubuntu.com",
    "ports.ubuntu.com",
)


def _backup_root(ctx: InstallContext) -> Path:
    return ctx.state_path.parent / _BACKUP_DIRNAME


def _uri(ctx: InstallContext) -> str:
    mirror = ctx.manifest.apt_mirror
    if ctx.host_arch == "amd64":
        return mirror["amd64_uri"]
    if ctx.host_arch == "arm64":
        return mirror["arm64_uri"]
    raise OslabError(f"无法为不支持的架构选择 APT 镜像：{ctx.host_arch}")


def _metadata_path(ctx: InstallContext) -> Path:
    return _backup_root(ctx) / "metadata.json"


def _install_text(destination: Path, content: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix="oslab-apt-source-", suffix=".tmp")
    os.close(descriptor)
    temporary = Path(temporary_name)
    temporary.write_text(content, encoding="utf-8")
    try:
        run(["sudo", "install", "-m", "0644", str(temporary), str(destination)], capture=False)
    finally:
        temporary.unlink(missing_ok=True)


def _is_official_ubuntu_uri(value: str) -> bool:
    hostname = (urlparse(value).hostname or "").lower()
    return any(hostname == item or hostname.endswith("." + item) for item in _OFFICIAL_UBUNTU_HOSTS)


def _rewrite_line(line: str, uri: str) -> str:
    stripped = line.lstrip()
    if stripped.startswith("URIs:"):
        prefix, values = line.split(":", 1)
        replaced = [uri if _is_official_ubuntu_uri(value) else value for value in values.split()]
        return prefix + ": " + " ".join(replaced)
    if stripped.startswith("deb ") or stripped.startswith("deb-src "):
        return re.sub(
            r"https?://[^\s]+",
            lambda match: uri if _is_official_ubuntu_uri(match.group(0)) else match.group(0),
            line,
        )
    return line


def _rewrite(content: str, uri: str) -> str:
    return "\n".join(_rewrite_line(line, uri) for line in content.splitlines()) + (
        "\n" if content.endswith("\n") else ""
    )


def _active_uris(content: str) -> tuple[str, ...]:
    """只提取生效的 APT 条目，忽略注释中的示例或旧地址。"""
    values: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("URIs:"):
            values.extend(stripped.split(":", 1)[1].split())
        elif stripped.startswith("deb ") or stripped.startswith("deb-src "):
            values.extend(match.group(0) for match in re.finditer(r"https?://[^\s]+", stripped))
    return tuple(values)


def _contains_official_source(content: str) -> bool:
    return any(_is_official_ubuntu_uri(value) for value in _active_uris(content))


def is_active(ctx: InstallContext) -> bool:
    uri = _uri(ctx)
    contents = [path.read_text(encoding="utf-8") for path in _MANAGED_FILES if path.exists()]
    normalized = uri.rstrip("/")
    return bool(contents) and any(
        any(value.rstrip("/") == normalized for value in _active_uris(content))
        for content in contents
    ) and not any(
        _contains_official_source(content) for content in contents
    )


def enable(ctx: InstallContext) -> None:
    if _backup_root(ctx).exists():
        logger.warning("检测到上次安装遗留的 APT 源备份；先恢复后重新切换。")
        restore(ctx)
    candidates = [path for path in _MANAGED_FILES if path.exists()]
    if not candidates:
        raise OslabError("未找到可管理的 Ubuntu APT 源文件：/etc/apt/sources.list 或 ubuntu.sources")
    backup_root = _backup_root(ctx)
    logger.info("临时切换 APT 源到阿里云镜像：%s", _uri(ctx))
    run(["sudo", "mkdir", "-p", str(backup_root)], capture=False)
    metadata = {
        "files": [
            {"path": str(path), "backup": path.name}
            for path in candidates
        ]
    }
    for path in candidates:
        run(["sudo", "cp", "-p", str(path), str(backup_root / path.name)], capture=False)
    _install_text(_metadata_path(ctx), json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    for path in candidates:
        rewritten = _rewrite(path.read_text(encoding="utf-8"), _uri(ctx))
        if rewritten == path.read_text(encoding="utf-8"):
            logger.warning("源文件未发现可替换 URI，保持内容不变：%s", path)
        else:
            _install_text(path, rewritten)
            logger.debug("已切换源文件：%s", path)
    logger.info("APT 源切换完成；安装结束后会自动恢复原始配置。")


def restore(ctx: InstallContext) -> None:
    metadata_path = _metadata_path(ctx)
    if not metadata_path.exists():
        backup_root = _backup_root(ctx)
        if not backup_root.exists():
            logger.debug("不存在 APT 源备份，无需恢复。")
            return
        logger.warning("APT 备份元数据缺失，将按已知文件名执行保守恢复。")
        records = [
            {"path": str(path), "backup": path.name}
            for path in _MANAGED_FILES
            if (backup_root / path.name).exists()
        ]
        if not records:
            raise OslabError(f"APT 备份目录存在但没有可恢复文件：{backup_root}")
    else:
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            records = metadata["files"]
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise OslabError(f"无法读取 APT 源备份元数据：{metadata_path}") from error
    backup_root = _backup_root(ctx)
    logger.info("恢复安装前的 APT 源配置。")
    for record in records:
        try:
            path = Path(record["path"])
            backup_name = record["backup"]
        except (KeyError, TypeError) as error:
            raise OslabError("APT 备份元数据中的文件记录格式无效") from error
        if path not in _MANAGED_FILES:
            raise OslabError(f"APT 备份元数据包含不受管理的路径：{path}")
        if backup_name != path.name:
            raise OslabError(f"APT 备份元数据包含无效备份文件名：{backup_name}")
        backup = backup_root / backup_name
        if not backup.exists():
            raise OslabError(f"APT 源备份文件缺失：{backup}")
        run(["sudo", "cp", "-p", str(backup), str(path)], capture=False)
        logger.debug("已恢复源文件：%s", path)
    run(["sudo", "rm", "-rf", str(backup_root)], capture=False)
    logger.info("APT 源已恢复为安装前配置。")
