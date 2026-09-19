from oslab_setup.context import InstallContext
from oslab_setup.core.platform import require_supported
from oslab_setup.verify._base import VerifyStage


class PlatformVerifyStage(VerifyStage):
    name = "platform"

    def check(self, ctx: InstallContext) -> None:
        require_supported(ctx.platform, ctx.manifest.ubuntu_version, ctx.manifest.architectures)
