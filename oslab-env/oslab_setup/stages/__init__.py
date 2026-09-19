import importlib.util
import sys
from pathlib import Path

from oslab_setup.stages._base import Stage


_STAGE_FILES = (
    ("00-preflight.py", "PreflightStage"),
    ("05-apt_mirror.py", "AptMirrorStage"),
    ("10-system_packages.py", "SystemPackagesStage"),
    ("20-riscv_toolchain.py", "RiscvToolchainStage"),
    ("30-qemu.py", "QemuStage"),
    ("40-debug_tools.py", "DebugToolsStage"),
    ("50-rust.py", "RustStage"),
    ("60-environment.py", "EnvironmentStage"),
    ("100-finalize.py", "FinalizeStage"),
)


def _load_stage(filename: str, class_name: str) -> Stage:
    path = Path(__file__).with_name(filename)
    module_name = f"{__name__}._loaded_{filename.replace('-', '_').replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载安装阶段文件：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)()


STAGES: tuple[Stage, ...] = tuple(_load_stage(*spec) for spec in _STAGE_FILES)


def stage_by_name(name: str | None) -> Stage:
    for stage in STAGES:
        if stage.name == name:
            return stage
    raise ValueError(f"未知安装阶段：{name}")
