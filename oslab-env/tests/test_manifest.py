import unittest
import logging
from dataclasses import replace
from pathlib import Path

from oslab_setup.context import InstallContext
from oslab_setup.core.log import ColorFormatter
from oslab_setup.core.manifest import load_manifest
from oslab_setup.errors import OslabError
from oslab_setup import stages
from oslab_setup import verify


ROOT = Path(__file__).resolve().parents[1]


class ManifestTests(unittest.TestCase):
    def test_checked_in_manifest_loads(self) -> None:
        manifest = load_manifest(ROOT)
        self.assertEqual(manifest.architectures, ("amd64", "arm64"))
        self.assertEqual(manifest.environment_version, "2026.1-dev")

    def test_required_apt_packages_and_rust_contract_are_declared(self) -> None:
        manifest = load_manifest(ROOT)
        self.assertIn("gcc-riscv64-unknown-elf", manifest.packages_for("riscv_gnu"))
        self.assertIn("binutils-riscv64-unknown-elf", manifest.packages_for("riscv_gnu"))
        self.assertIn("qemu-system-riscv", manifest.packages_for("qemu"))
        self.assertIn("opensbi", manifest.packages_for("qemu"))
        self.assertEqual(manifest.versions["rust"]["toolchain"], "nightly-2026-09-01")
        self.assertIn("riscv64imac-unknown-none-elf", manifest.versions["rust"]["targets"])

    def test_readme_lists_every_required_apt_package(self) -> None:
        manifest = load_manifest(ROOT)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        missing = [
            package
            for group in manifest.packages.values()
            for package in group
            if package not in readme
        ]
        self.assertEqual(missing, [])

    def test_context_uses_the_checked_in_manifest(self) -> None:
        context = InstallContext.create(ROOT)
        self.assertEqual(context.root, ROOT)
        self.assertEqual(context.manifest.environment_version, "2026.1-dev")

    def test_tested_lock_pins_every_apt_package(self) -> None:
        context = InstallContext.create(ROOT)
        required = {
            package
            for group in context.manifest.packages.values()
            for package in group
        }
        lock = {
            "status": "tested",
            "environment_version": context.environment_version,
            "architecture": context.host_arch,
            "packages": {
                "qemu_package": context.manifest.versions["qemu"]["apt_package"],
                "riscv_gnu_gcc_package": context.manifest.versions["riscv_gnu"]["gcc_package"],
                "riscv_gnu_binutils_package": context.manifest.versions["riscv_gnu"]["binutils_package"],
                "rust_toolchain": context.manifest.versions["rust"]["toolchain"],
            },
            "apt_versions": {package: "1.2.3-test" for package in required},
        }
        tested = replace(context, lock=lock)
        tested.validate_tested_lock()
        self.assertTrue(all(item.endswith("=1.2.3-test") for item in tested.packages_for_install("qemu")))

    def test_tested_lock_rejects_an_incomplete_apt_version_set(self) -> None:
        context = InstallContext.create(ROOT)
        incomplete = replace(
            context,
            lock={
                "status": "tested",
                "environment_version": context.environment_version,
                "architecture": context.host_arch,
                "packages": {
                    "qemu_package": context.manifest.versions["qemu"]["apt_package"],
                    "riscv_gnu_gcc_package": context.manifest.versions["riscv_gnu"]["gcc_package"],
                    "riscv_gnu_binutils_package": context.manifest.versions["riscv_gnu"]["binutils_package"],
                    "rust_toolchain": context.manifest.versions["rust"]["toolchain"],
                },
                "apt_versions": {},
            },
        )
        with self.assertRaises(OslabError):
            incomplete.validate_tested_lock()

    def test_stage_files_and_registry_have_a_fixed_order(self) -> None:
        self.assertEqual(
            tuple(filename for filename, _ in stages._STAGE_FILES),
            (
                "00-preflight.py",
                "05-apt_mirror.py",
                "10-system_packages.py",
                "20-riscv_toolchain.py",
                "30-qemu.py",
                "40-debug_tools.py",
                "50-rust.py",
                "60-environment.py",
                "100-finalize.py",
            ),
        )
        self.assertEqual(
            tuple(stage.name for stage in stages.STAGES),
            (
                "preflight",
                "apt-mirror",
                "system-packages",
                "riscv-toolchain",
                "qemu",
                "debug-tools",
                "rust",
                "environment",
                "finalize",
            ),
        )
        self.assertEqual(verify.VERIFY_STAGES[0].name, "platform")
        self.assertEqual(verify.VERIFY_STAGES[-1].name, "smoke")
        self.assertIn("environment", tuple(stage.name for stage in verify.VERIFY_STAGES))

    def test_colored_logger_uses_the_specified_level_colors(self) -> None:
        formatter = ColorFormatter(color=True)
        levels_and_colors = (
            (5, "\033[37m"),
            (logging.DEBUG, "\033[34m"),
            (logging.INFO, "\033[32m"),
            (logging.WARNING, "\033[33m"),
            (logging.ERROR, "\033[31m"),
        )
        for level, color in levels_and_colors:
            record = logging.LogRecord("oslab_setup", level, "", 0, "测试日志", (), None)
            self.assertTrue(formatter.format(record).startswith(color))


if __name__ == "__main__":
    unittest.main()
