import argparse
import shutil
from pathlib import Path
from typing import Callable

from oslab_setup.context import InstallContext
from oslab_setup.core import apt_sources
from oslab_setup.core.platform import require_supported
from oslab_setup.errors import OslabError
from oslab_setup.core.log import configure, logger
from oslab_setup.stages import STAGES, stage_by_name
from oslab_setup.verify import VERIFY_STAGES, verify_by_name


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m oslab_setup",
        description="安装、检查和验证版本化的 OSLab 开发环境。",
    )
    parser.add_argument(
        "--log-level",
        choices=("trace", "debug", "info", "warning", "error"),
        default="info",
        help="控制台日志级别（默认：info）。",
    )
    parser.add_argument("--no-color", action="store_true", help="关闭日志颜色。")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("install", "verify"):
        command = sub.add_parser(name)
        command.add_argument(
            "--stage",
            choices=[stage.name for stage in (STAGES if name == "install" else VERIFY_STAGES)],
            help="仅执行指定阶段；安装时仍会先执行平台预检。",
        )
    sub.add_parser("info", help="显示当前解析出的环境定义。")
    sub.add_parser("doctor", help="执行不修改系统的诊断。")
    sub.add_parser("bootstrap-check", help=argparse.SUPPRESS)
    mirror = sub.add_parser("apt-mirror", help="临时切换或恢复受管 APT 镜像源。")
    mirror.add_argument("action", choices=("enable", "restore"), help="切换到镜像或恢复原始源。")
    return parser


def _run_install(ctx: InstallContext, selected: str | None) -> None:
    stages = [stage_by_name(selected)] if selected else STAGES
    logger.info("开始安装流程：环境版本=%s，宿主架构=%s，阶段数=%d", ctx.environment_version, ctx.host_arch, len(stages))
    if selected and selected != "preflight":
        logger.info("指定了阶段 %s；先执行必需的平台预检。", selected)
        stage_by_name("preflight").ensure(ctx)
    failure_pending = False
    try:
        for stage in stages:
            stage.ensure(ctx)
    except BaseException:
        failure_pending = True
        raise
    finally:
        try:
            apt_sources.restore(ctx)
        except OslabError as restore_error:
            if not failure_pending:
                raise
            logger.error("安装已经失败，随后恢复 APT 源时再次失败：%s", restore_error)
            logger.error("退出后 bootstrap 清理钩子会再尝试一次恢复；若仍失败，请保留日志并联系课程助教。")


def _run_verify(ctx: InstallContext, selected: str | None) -> None:
    stages = [verify_by_name(selected)] if selected else VERIFY_STAGES
    logger.info("开始验证流程：环境版本=%s，验证项数=%d", ctx.environment_version, len(stages))
    for stage in stages:
        stage.verify(ctx)


def _info(ctx: InstallContext) -> None:
    logger.info("OSLab 环境版本：%s", ctx.environment_version)
    logger.info("仓库目录：%s", ctx.root)
    logger.info("宿主架构：%s", ctx.host_arch)
    logger.info("检测到的系统：%s %s", ctx.platform.id, ctx.platform.version or "未知")
    logger.info("支持的架构：%s", ", ".join(ctx.manifest.architectures))
    logger.info("QEMU APT 包：%s", ctx.manifest.versions["qemu"]["apt_package"])
    logger.info(
        "RISC-V C 工具链：%s，%s",
        ctx.manifest.versions["riscv_gnu"]["gcc_package"],
        ctx.manifest.versions["riscv_gnu"]["binutils_package"],
    )
    logger.info("Rust 工具链：%s；目标：%s", ctx.manifest.versions["rust"]["toolchain"], ", ".join(ctx.manifest.versions["rust"]["targets"]))


def _doctor(ctx: InstallContext) -> None:
    def check_commands() -> None:
        missing = [item for item in ("sudo", "apt-get", "python3") if not shutil.which(item)]
        if missing:
            raise OslabError("缺少 bootstrap 命令：" + ", ".join(missing))

    checks: list[tuple[str, Callable[[], None]]] = [
        ("环境清单", lambda: ctx.manifest.validate()),
        (
            "系统平台",
            lambda: require_supported(
                ctx.platform,
                ctx.manifest.ubuntu_version,
                ctx.manifest.architectures,
            ),
        ),
        ("基础命令", check_commands),
    ]
    failures = 0
    for name, check in checks:
        try:
            check()
        except OslabError as error:
            failures += 1
            logger.error("诊断失败 [%s]：%s", name, error)
        else:
            logger.info("诊断通过 [%s]", name)
    if failures:
        raise OslabError(f"诊断发现 {failures} 个问题")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    configure(args.log_level, color=not args.no_color)
    try:
        logger.debug("正在创建安装上下文。")
        ctx = InstallContext.create(_root())
        logger.debug("安装上下文创建完成。")
        if args.command == "bootstrap-check":
            require_supported(ctx.platform, ctx.manifest.ubuntu_version, ctx.manifest.architectures)
            logger.info("Bootstrap 平台检查通过：Ubuntu %s %s。", ctx.platform.version, ctx.host_arch)
        elif args.command == "apt-mirror":
            if args.action == "enable":
                require_supported(ctx.platform, ctx.manifest.ubuntu_version, ctx.manifest.architectures)
                apt_sources.enable(ctx)
            else:
                apt_sources.restore(ctx)
        elif args.command == "install":
            _run_install(ctx, args.stage)
        elif args.command == "verify":
            _run_verify(ctx, args.stage)
        elif args.command == "info":
            _info(ctx)
        else:
            _doctor(ctx)
    except OslabError as error:
        logger.error("操作失败：%s", error)
        return 1
    return 0
