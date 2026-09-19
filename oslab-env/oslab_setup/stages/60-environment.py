import os
import tempfile
from pathlib import Path

from oslab_setup.context import InstallContext
from oslab_setup.core.filesystem import install_profile
from oslab_setup.errors import OslabError
from oslab_setup.core.log import logger
from oslab_setup.stages._base import Stage


class EnvironmentStage(Stage):
    name = "environment"

    def check(self, ctx: InstallContext) -> None:
        profile = "/etc/profile.d/oslab.sh"
        try:
            content = Path(profile).read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise OslabError(f"缺少 OSLab shell 环境脚本：{profile}") from error
        expected = f'export OSLAB_ENVIRONMENT_VERSION="{ctx.environment_version}"'
        if expected not in content:
            raise OslabError("OSLab shell 环境脚本未导出期望的环境版本")
        target = ctx.manifest.versions["rust"]["targets"][0]
        if f'export OSLAB_RUST_TARGET="{target}"' not in content:
            raise OslabError("OSLab shell 环境脚本未导出期望的 Rust target")

    def run(self, ctx: InstallContext) -> None:
        source = ctx.root / "templates" / "oslab.sh"
        content = source.read_text(encoding="utf-8")
        replacements = {
            "@OSLAB_ENVIRONMENT_VERSION@": ctx.environment_version,
            "@OSLAB_RUST_TOOLCHAIN@": ctx.manifest.versions["rust"]["toolchain"],
            "@OSLAB_RUST_TARGET@": ctx.manifest.versions["rust"]["targets"][0],
        }
        for token, value in replacements.items():
            content = content.replace(token, value)
        logger.debug("生成环境脚本，注入环境版本：%s", ctx.environment_version)
        descriptor, temporary_name = tempfile.mkstemp(prefix="oslab-profile-", suffix=".sh")
        os.close(descriptor)
        temporary = Path(temporary_name)
        temporary.write_text(content, encoding="utf-8")
        try:
            install_profile(temporary)
        finally:
            temporary.unlink(missing_ok=True)
