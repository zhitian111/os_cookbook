import importlib.util
import sys
from pathlib import Path

from oslab_setup.verify._base import VerifyStage


_VERIFY_FILES = (
    ("00-platform.py", "PlatformVerifyStage"),
    ("10-system_tools.py", "SystemToolsVerifyStage"),
    ("20-riscv_toolchain.py", "RiscvToolchainVerifyStage"),
    ("30-qemu.py", "QemuVerifyStage"),
    ("40-rust.py", "RustVerifyStage"),
    ("50-environment.py", "EnvironmentVerifyStage"),
    ("100-smoke.py", "SmokeVerifyStage"),
)


def _load_verify_stage(filename: str, class_name: str) -> VerifyStage:
    path = Path(__file__).with_name(filename)
    module_name = f"{__name__}._loaded_{filename.replace('-', '_').replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载验证阶段文件：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)()


VERIFY_STAGES: tuple[VerifyStage, ...] = tuple(_load_verify_stage(*spec) for spec in _VERIFY_FILES)


def verify_by_name(name: str | None) -> VerifyStage:
    for stage in VERIFY_STAGES:
        if stage.name == name:
            return stage
    raise ValueError(f"未知验证阶段：{name}")
