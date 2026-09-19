import shutil

from oslab_setup.context import InstallContext
from oslab_setup.errors import VerificationError
from oslab_setup.core.log import logger
from oslab_setup.verify._base import VerifyStage


class SystemToolsVerifyStage(VerifyStage):
    name = "system-tools"

    def check(self, ctx: InstallContext) -> None:
        required = ("git", "cmake", "make", "gdb-multiarch", "dtc")
        missing = [tool for tool in required if not shutil.which(tool)]
        if missing:
            raise VerificationError("所需系统工具不可用：" + ", ".join(missing))
        logger.debug("系统工具验证通过：%s", ", ".join(required))
