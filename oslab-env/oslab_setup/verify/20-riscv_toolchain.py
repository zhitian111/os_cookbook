from oslab_setup.context import InstallContext
from oslab_setup.stages import stage_by_name
from oslab_setup.verify._base import VerifyStage


class RiscvToolchainVerifyStage(VerifyStage):
    name = "riscv-toolchain"

    def check(self, ctx: InstallContext) -> None:
        stage_by_name("riscv-toolchain").check(ctx)
