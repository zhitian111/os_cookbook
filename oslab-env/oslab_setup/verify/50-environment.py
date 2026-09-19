from oslab_setup.context import InstallContext
from oslab_setup.stages import stage_by_name
from oslab_setup.verify._base import VerifyStage


class EnvironmentVerifyStage(VerifyStage):
    name = "environment"

    def check(self, ctx: InstallContext) -> None:
        stage_by_name("environment").check(ctx)
