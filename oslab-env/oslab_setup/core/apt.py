from oslab_setup.core.command import run
from oslab_setup.core.log import logger, trace


def install(packages: tuple[str, ...]) -> None:
    if packages:
        logger.info("准备通过 APT 安装 %d 个软件包：%s", len(packages), ", ".join(packages))
        run(["sudo", "apt-get", "install", "-y", *packages], capture=False)


def installed(package: str) -> bool:
    result = run(["dpkg-query", "-s", package], check=False)
    present = result.stdout.find("Status: install ok installed") >= 0
    trace("APT 软件包检查：%s，已安装=%s", package, present)
    return present


def version(package: str) -> str:
    result = run(["dpkg-query", "-W", package], check=False)
    fields = result.stdout.strip().split()
    if len(fields) < 2:
        return "未安装"
    return fields[1]
