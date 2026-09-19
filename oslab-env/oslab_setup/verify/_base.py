"""验证阶段公共接口。"""

from abc import ABC, abstractmethod

from oslab_setup.context import InstallContext
from oslab_setup.core.log import logger


class VerifyStage(ABC):
    name: str

    @abstractmethod
    def check(self, ctx: InstallContext) -> None:
        """Raise an OslabError if the component does not verify."""

    def verify(self, ctx: InstallContext) -> None:
        logger.debug("开始验证项 %s。", self.name)
        self.check(ctx)
        logger.info("验证项 %s 通过。", self.name)
