import shutil
from pathlib import Path

from oslab_setup.context import InstallContext
from oslab_setup.core import apt
from oslab_setup.core.command import run
from oslab_setup.errors import OslabError
from oslab_setup.core.log import logger
from oslab_setup.stages._base import Stage


class RiscvToolchainStage(Stage):
    name = "riscv-toolchain"

    def check(self, ctx: InstallContext) -> None:
        missing_packages = [item for item in ctx.manifest.packages_for("riscv_gnu") if not apt.installed(item)]
        if missing_packages:
            raise OslabError("缺少 RISC-V APT 软件包：" + ", ".join(missing_packages))
        prefix = ctx.manifest.versions["riscv_gnu"]["binutils_prefix"]
        required = (
            ctx.manifest.versions["riscv_gnu"]["gcc_executable"],
            f"{prefix}-as", f"{prefix}-ld", f"{prefix}-objcopy",
            f"{prefix}-objdump", f"{prefix}-readelf", f"{prefix}-nm",
        )
        missing_tools = [tool for tool in required if not shutil.which(tool)]
        if missing_tools:
            raise OslabError("RISC-V 工具链缺少可执行程序：" + ", ".join(missing_tools))
        compiler = Path(shutil.which(required[0]) or "").resolve()
        if compiler.parent != Path("/usr/bin"):
            raise OslabError(f"RISC-V 编译器不是 APT 管理的 /usr/bin 程序：{compiler}")
        version = run([str(compiler), "--version"]).stdout.splitlines()[0]
        logger.debug("RISC-V GNU 工具链检查通过：%s；%s", ", ".join(required), version)

    def run(self, ctx: InstallContext) -> None:
        apt.install(ctx.packages_for_install("riscv_gnu"))
