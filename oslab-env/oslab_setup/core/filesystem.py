from pathlib import Path

from oslab_setup.core.command import run
from oslab_setup.core.log import logger


def install_profile(source: Path) -> None:
    logger.info("安装 shell 环境脚本：%s -> /etc/profile.d/oslab.sh", source)
    run(["sudo", "install", "-m", "0644", str(source), "/etc/profile.d/oslab.sh"], capture=False)
