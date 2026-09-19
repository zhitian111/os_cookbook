import json
import os
import tempfile
from pathlib import Path

from oslab_setup.core.command import run
from oslab_setup.core.log import logger, trace


def read(path: Path) -> dict[str, object] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        trace("未找到安装状态文件：%s", path)
        return None
    except json.JSONDecodeError:
        logger.warning("安装状态文件不是有效 JSON，将视为未安装：%s", path)
        return None


def write(path: Path, payload: dict[str, object]) -> None:
    logger.info("写入 OSLab 安装状态：%s", path)
    descriptor, temporary_name = tempfile.mkstemp(prefix="oslab-state-", suffix=".json")
    os.close(descriptor)
    temporary = Path(temporary_name)
    temporary.unlink(missing_ok=True)
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    run(["sudo", "mkdir", "-p", str(path.parent)], capture=False)
    run(["sudo", "install", "-m", "0644", str(temporary), str(path)], capture=False)
    temporary.unlink(missing_ok=True)
