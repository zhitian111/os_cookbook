from oslab_setup.context import InstallContext
from oslab_setup.core.command import run
from oslab_setup.core.log import logger
from oslab_setup.errors import VerificationError
from oslab_setup.verify._base import VerifyStage


class SmokeVerifyStage(VerifyStage):
    name = "smoke"

    def check(self, ctx: InstallContext) -> None:
        compiler_name = ctx.manifest.versions["riscv_gnu"]["gcc_executable"]
        qemu_name = ctx.manifest.versions["qemu"]["executable"]
        compiler = compiler_name
        qemu = qemu_name
        smoke_dir = ctx.root / "smoke"
        toolchain = ctx.manifest.versions["rust"]["toolchain"]
        rust_target = ctx.manifest.versions["rust"]["targets"][0]
        logger.info("开始实际 RISC-V smoke test。")
        logger.debug("smoke 编译器：%s；QEMU：%s；目录：%s", compiler, qemu, smoke_dir)
        run(["make", "-C", str(smoke_dir), "clean"], capture=False)
        run(
            [
                "/usr/bin/rustc",
                f"+{toolchain}",
                "--target",
                rust_target,
                "--crate-type",
                "staticlib",
                "-C",
                "panic=abort",
                str(smoke_dir / "rust" / "lib.rs"),
                "-o",
                str(smoke_dir / "rust" / "liboslab_rust_smoke.a"),
            ],
            capture=False,
        )
        logger.info("Rust no_std RISC-V target 编译通过。")
        run(["make", "-C", str(smoke_dir), f"RISCV_GCC={compiler}"], capture=False)
        result = run(
            [
                qemu,
                "-machine",
                "virt",
                "-nographic",
                "-bios",
                "default",
                "-kernel",
                str(smoke_dir / "build" / "oslab-smoke.elf"),
                "-monitor",
                "none",
                "-serial",
                "stdio",
            ],
            timeout=20,
        )
        output = result.stdout + result.stderr
        if "OSLAB_SMOKE_OK" not in output:
            raise VerificationError("RISC-V smoke test 未输出 OSLAB_SMOKE_OK")
        logger.info("RISC-V smoke test 已输出 OSLAB_SMOKE_OK。")
