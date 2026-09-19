from oslab_setup.context import InstallContext
from oslab_setup.core import apt_sources
from oslab_setup.core.command import run
from oslab_setup.errors import OslabError
from oslab_setup.core.log import logger
from oslab_setup.stages._base import Stage


class AptMirrorStage(Stage):
    name = "apt-mirror"

    def check(self, ctx: InstallContext) -> None:
        if not apt_sources.is_active(ctx):
            raise OslabError("阿里云 APT 镜像尚未启用")

    def run(self, ctx: InstallContext) -> None:
        apt_sources.enable(ctx)
        logger.info("使用阿里云镜像更新 APT 索引。")
        run(["sudo", "apt-get", "update"], capture=False)
