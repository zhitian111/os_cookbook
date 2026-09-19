from oslab_setup.context import InstallContext
from oslab_setup.core import apt
from oslab_setup.core.command import run
from oslab_setup.core.state import read, write
from oslab_setup.errors import OslabError
from oslab_setup.core.log import logger
from oslab_setup.stages._base import Stage


class FinalizeStage(Stage):
    name = "finalize"

    def check(self, ctx: InstallContext) -> None:
        state = read(ctx.state_path)
        if state is None:
            raise OslabError("缺少 OSLab 安装状态文件")
        if state.get("environment_version") != ctx.environment_version:
            raise OslabError("OSLab 安装状态文件中的环境版本不匹配")
        if state.get("host_arch") != ctx.host_arch:
            raise OslabError("OSLab 安装状态文件中的宿主架构不匹配")

    def run(self, ctx: InstallContext) -> None:
        package_names = tuple(
            dict.fromkeys(
                package
                for group in ctx.manifest.packages.values()
                for package in group
            )
        )
        write(
            ctx.state_path,
            {
                "environment_version": ctx.environment_version,
                "host_arch": ctx.host_arch,
                "installed": {
                    "apt_versions": {
                        package: apt.version(package)
                        for package in package_names
                    },
                    "rust_toolchain": run(
                        [
                            "/usr/bin/rustc",
                            f"+{ctx.manifest.versions['rust']['toolchain']}",
                            "--version",
                        ]
                    ).stdout.strip(),
                },
            },
        )
        logger.info("安装完成。请新开终端或执行 source /etc/profile.d/oslab.sh，然后运行 bash ./verify.sh。")
