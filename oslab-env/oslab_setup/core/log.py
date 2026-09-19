"""OSLab 安装器唯一的控制台日志器。"""

import logging
import sys


TRACE = 5
logging.addLevelName(TRACE, "TRACE")

_COLORS = {
    TRACE: "\033[37m",
    logging.DEBUG: "\033[34m",
    logging.INFO: "\033[32m",
    logging.WARNING: "\033[33m",
    logging.ERROR: "\033[31m",
    logging.CRITICAL: "\033[31m",
}
_RESET = "\033[0m"


class ColorFormatter(logging.Formatter):
    def __init__(self, color: bool) -> None:
        super().__init__("%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
        self.color = color

    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        if not self.color:
            return text
        return f"{_COLORS.get(record.levelno, _RESET)}{text}{_RESET}"


logger = logging.getLogger("oslab_setup")


def configure(level_name: str = "info", color: bool = True) -> None:
    """配置唯一 logger；可安全地在测试或嵌入式调用中重复执行。"""
    level = TRACE if level_name == "trace" else getattr(logging, level_name.upper())
    logger.setLevel(level)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        logger.addHandler(handler)
    for handler in logger.handlers:
        handler.setLevel(level)
        handler.setFormatter(ColorFormatter(color))


def trace(message: str, *args: object) -> None:
    logger.log(TRACE, message, *args)
