import shutil

from oslab_setup.context import InstallContext
from oslab_setup.core.command import run
from oslab_setup.core.log import logger
from oslab_setup.core.platform import require_supported
from oslab_setup.errors import OslabError
from oslab_setup.stages._base import Stage


class PreflightStage(Stage):
    name = "preflight"

    def check(self, ctx: InstallContext) -> None:
        logger.info("预检：验证清单、Ubuntu 版本、宿主架构和提权能力。")
        ctx.manifest.validate()
        require_supported(ctx.platform, ctx.manifest.ubuntu_version, ctx.manifest.architectures)
        if not ctx.lock_is_tested:
            if ctx.environment_version.endswith("-dev"):
                logger.warning("当前是开发环境且 lock 尚未验证；APT 将使用仓库当前版本。")
            else:
                raise OslabError("正式环境必须提供当前架构且 status=tested 的 lock 文件")
        else:
            ctx.validate_tested_lock()
            logger.info("当前架构的 tested lock 完整且与清单一致；APT 将安装锁定版本。")
        missing = [command for command in ("sudo", "apt-get", "curl") if not shutil.which(command)]
        if missing:
            raise OslabError(
                "基础条件不满足，缺少命令："
                + ", ".join(missing)
                + "。请确认系统是完整 Ubuntu，或先使用系统安装介质补齐。"
            )
        run(["sudo", "-v"], capture=False)

    def run(self, ctx: InstallContext) -> None:
        self.check(ctx)
