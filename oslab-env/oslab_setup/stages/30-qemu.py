import shutil
from pathlib import Path

from oslab_setup.context import InstallContext
from oslab_setup.core import apt
from oslab_setup.core.command import run
from oslab_setup.errors import OslabError
from oslab_setup.core.log import logger
from oslab_setup.stages._base import Stage


class QemuStage(Stage):
    name = "qemu"

    def check(self, ctx: InstallContext) -> None:
        missing_packages = [item for item in ctx.manifest.packages_for("qemu") if not apt.installed(item)]
        if missing_packages:
            raise OslabError("缺少 QEMU/OpenSBI APT 软件包：" + ", ".join(missing_packages))
        executable = ctx.manifest.versions["qemu"]["executable"]
        binary = shutil.which(executable)
        if not binary:
            raise OslabError(f"未找到 QEMU 可执行程序：{executable}")
        resolved = Path(binary).resolve()
        if resolved.parent != Path("/usr/bin"):
            raise OslabError(f"QEMU 不是 APT 管理的 /usr/bin 程序：{resolved}")
        version = run([str(resolved), "--version"]).stdout.splitlines()[0]
        logger.debug("QEMU 检查通过：%s；%s", resolved, version)

    def run(self, ctx: InstallContext) -> None:
        apt.install(ctx.packages_for_install("qemu"))
