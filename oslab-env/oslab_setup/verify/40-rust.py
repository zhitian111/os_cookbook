from oslab_setup.context import InstallContext
from oslab_setup.errors import OslabError, VerificationError
from oslab_setup.stages import stage_by_name
from oslab_setup.verify._base import VerifyStage


class RustVerifyStage(VerifyStage):
    name = "rust"

    def check(self, ctx: InstallContext) -> None:
        try:
            stage_by_name("rust").check(ctx)
        except OslabError as error:
            raise VerificationError(str(error)) from error
