from dataclasses import dataclass
from pathlib import Path
import tomllib

from oslab_setup.core.manifest import Manifest, load_manifest
from oslab_setup.core.platform import Platform, detect_platform
from oslab_setup.core.log import logger
from oslab_setup.errors import OslabError


@dataclass(frozen=True)
class InstallContext:
    root: Path
    platform: Platform
    manifest: Manifest
    lock: dict[str, object]
    state_path: Path = Path("/var/lib/oslab/state.json")

    @property
    def host_arch(self) -> str:
        return self.platform.architecture

    @property
    def environment_version(self) -> str:
        return self.manifest.environment_version

    @property
    def lock_is_tested(self) -> bool:
        return self.lock.get("status") == "tested"

    def packages_for_install(self, group: str) -> tuple[str, ...]:
        versions = self.lock.get("apt_versions", {}) if self.lock_is_tested else {}
        return tuple(
            f"{package}={versions[package]}" if package in versions else package
            for package in self.manifest.packages_for(group)
        )

    def validate_tested_lock(self) -> None:
        """确认正式 lock 与当前清单完整对应，避免部分软件包悄悄回退为滚动版本。"""
        if self.lock.get("environment_version") != self.environment_version:
            raise OslabError("lock 中的环境版本与 platform.toml 不一致")
        if self.lock.get("architecture") != self.host_arch:
            raise OslabError("lock 中的宿主架构与当前主机不一致")
        expected_contract = {
            "qemu_package": self.manifest.versions["qemu"]["apt_package"],
            "riscv_gnu_gcc_package": self.manifest.versions["riscv_gnu"]["gcc_package"],
            "riscv_gnu_binutils_package": self.manifest.versions["riscv_gnu"]["binutils_package"],
            "rust_toolchain": self.manifest.versions["rust"]["toolchain"],
        }
        if self.lock.get("packages") != expected_contract:
            raise OslabError("lock 中的关键工具契约与 versions.toml 不一致")
        required = {
            package
            for group in self.manifest.packages.values()
            for package in group
        }
        versions = self.lock.get("apt_versions")
        if not isinstance(versions, dict) or set(versions) != required:
            missing = sorted(required - set(versions or {})) if isinstance(versions, dict) else sorted(required)
            extra = sorted(set(versions or {}) - required) if isinstance(versions, dict) else []
            raise OslabError(f"lock 的 APT 版本列表不完整：缺少={missing}，多余={extra}")
        invalid = sorted(package for package, version in versions.items() if not isinstance(version, str) or not version)
        if invalid:
            raise OslabError("lock 包含空或无效的 APT 版本：" + ", ".join(invalid))

    @classmethod
    def create(cls, root: Path) -> "InstallContext":
        logger.debug("创建安装上下文，仓库根目录：%s", root)
        platform = detect_platform()
        manifest = load_manifest(root)
        lock_path = root / "lock" / f"{platform.architecture}.lock.toml"
        if lock_path.exists():
            with lock_path.open("rb") as handle:
                lock = tomllib.load(handle)
        else:
            lock = {"status": "missing"}
        result = cls(root=root, platform=platform, manifest=manifest, lock=lock)
        logger.debug("安装上下文就绪：lock 状态=%s", result.lock.get("status", "missing"))
        return result
