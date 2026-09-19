from oslab_setup.context import InstallContext
from oslab_setup.core import apt
from oslab_setup.errors import OslabError
from oslab_setup.core.log import logger
from oslab_setup.stages._base import Stage


class SystemPackagesStage(Stage):
    name = "system-packages"

    def check(self, ctx: InstallContext) -> None:
        missing = [package for package in ctx.manifest.packages_for("base") if not apt.installed(package)]
        if missing:
            logger.warning("基础 APT 软件包缺失：%s", ", ".join(missing))
            raise OslabError("缺少基础 APT 软件包：" + ", ".join(missing))

    def run(self, ctx: InstallContext) -> None:
        apt.install(ctx.packages_for_install("base"))
