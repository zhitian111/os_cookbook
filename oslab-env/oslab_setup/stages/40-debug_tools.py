from oslab_setup.context import InstallContext
from oslab_setup.core import apt
from oslab_setup.errors import OslabError
from oslab_setup.core.log import logger
from oslab_setup.stages._base import Stage


class DebugToolsStage(Stage):
    name = "debug-tools"

    def check(self, ctx: InstallContext) -> None:
        packages = ctx.manifest.packages_for("debug")
        missing = [package for package in packages if not apt.installed(package)]
        if missing:
            raise OslabError("缺少调试工具软件包：" + ", ".join(missing))
        logger.debug("调试工具软件包已安装：%s", ", ".join(packages))

    def run(self, ctx: InstallContext) -> None:
        apt.install(ctx.packages_for_install("debug"))
