from pathlib import Path

from oslab_setup.context import InstallContext
from oslab_setup.core.command import run
from oslab_setup.core import apt
from oslab_setup.errors import OslabError
from oslab_setup.core.log import logger
from oslab_setup.stages._base import Stage


class RustStage(Stage):
    name = "rust"

    def check(self, ctx: InstallContext) -> None:
        packages = ctx.manifest.packages_for("rust")
        missing_packages = [item for item in packages if not apt.installed(item)]
        if missing_packages:
            raise OslabError("缺少 Rust APT 软件包：" + ", ".join(missing_packages))
        missing_programs = [
            item
            for item in ctx.manifest.versions["rust"]["required_programs"]
            if not (Path("/usr/bin") / item).is_file()
        ]
        if missing_programs:
            raise OslabError("Rust APT 软件包未提供预期的 /usr/bin 程序：" + ", ".join(missing_programs))
        rustup = "/usr/bin/rustup"
        toolchain = ctx.manifest.versions["rust"]["toolchain"]
        installed = run([rustup, "toolchain", "list"]).stdout
        if toolchain not in installed:
            raise OslabError(f"未安装 Rust {toolchain} 工具链")
        targets = run([rustup, "target", "list", "--installed", "--toolchain", toolchain]).stdout
        missing_targets = [target for target in ctx.manifest.versions["rust"]["targets"] if target not in targets]
        if missing_targets:
            raise OslabError("Rust 缺少目标： " + ", ".join(missing_targets))
        components = run([rustup, "component", "list", "--installed", "--toolchain", toolchain]).stdout
        missing_components = [item for item in ctx.manifest.versions["rust"]["components"] if item not in components]
        if missing_components:
            raise OslabError("Rust 缺少组件： " + ", ".join(missing_components))
        rustc_version = run(["/usr/bin/rustc", f"+{toolchain}", "--version"]).stdout.strip()
        cargo_version = run(["/usr/bin/cargo", f"+{toolchain}", "--version"]).stdout.strip()
        logger.debug("Rust 工具链检查通过：%s；%s", rustc_version, cargo_version)

    def run(self, ctx: InstallContext) -> None:
        apt.install(ctx.packages_for_install("rust"))
        toolchain = ctx.manifest.versions["rust"]["toolchain"]
        profile = ctx.manifest.versions["rust"]["profile"]
        logger.info("为当前用户配置 Rust %s 工具链、目标和组件；不会修改全局默认工具链。", toolchain)
        rustup = "/usr/bin/rustup"
        run([rustup, "set", "profile", profile], capture=False)
        run([rustup, "toolchain", "install", toolchain, "--profile", profile], capture=False)
        for target in ctx.manifest.versions["rust"]["targets"]:
            run([rustup, "target", "add", "--toolchain", toolchain, target], capture=False)
        for component in ctx.manifest.versions["rust"]["components"]:
            run([rustup, "component", "add", "--toolchain", toolchain, component], capture=False)
