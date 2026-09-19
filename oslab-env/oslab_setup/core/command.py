import subprocess
from dataclasses import dataclass
from typing import Sequence

from oslab_setup.errors import OslabError
from oslab_setup.core.log import logger, trace


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    stdout: str
    stderr: str


def run(
    argv: Sequence[str],
    *,
    timeout: int | None = None,
    check: bool = True,
    capture: bool = True,
) -> CommandResult:
    printable = " ".join(argv)
    logger.debug("执行外部命令：%s", printable)
    trace("命令选项：超时=%s 秒，捕获输出=%s，失败即报错=%s", timeout, capture, check)
    try:
        completed = subprocess.run(
            list(argv),
            check=False,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            timeout=timeout,
        )
    except FileNotFoundError as error:
        raise OslabError(f"缺少所需命令：{argv[0]}") from error
    except subprocess.TimeoutExpired as error:
        raise OslabError(f"命令在 {timeout} 秒后超时：{printable}") from error
    result = CommandResult(tuple(argv), completed.stdout or "", completed.stderr or "")
    trace("命令退出码：%s", completed.returncode)
    if check and completed.returncode:
        details = result.stderr.strip() or result.stdout.strip()
        logger.warning("外部命令执行失败，退出码=%s：%s", completed.returncode, printable)
        raise OslabError(f"命令执行失败（退出码 {completed.returncode}）：{printable}\n{details}")
    return result
