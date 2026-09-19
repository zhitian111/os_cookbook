"""安装阶段公共接口。"""

from abc import ABC, abstractmethod

from oslab_setup.context import InstallContext
from oslab_setup.core.log import logger


class Stage(ABC):
    name: str

    @abstractmethod
    def check(self, ctx: InstallContext) -> None:
        """Raise an OslabError when this stage is not already satisfied."""

    @abstractmethod
    def run(self, ctx: InstallContext) -> None:
        """Make this stage true. Operations must be safe to retry."""

    def ensure(self, ctx: InstallContext) -> None:
        try:
            logger.debug("检查安装阶段 %s 是否已经满足。", self.name)
            self.check(ctx)
        except Exception as error:
            from oslab_setup.errors import OslabError

            if not isinstance(error, OslabError):
                raise
            logger.info("阶段 %s 未满足，将开始安装：%s", self.name, error)
            self.run(ctx)
            logger.debug("阶段 %s 安装动作结束，开始二次验证。", self.name)
            self.check(ctx)
            logger.info("阶段 %s 安装并验证通过。", self.name)
        else:
            logger.info("阶段 %s 已满足，跳过安装。", self.name)
