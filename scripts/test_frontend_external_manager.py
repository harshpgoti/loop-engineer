"""Behaviour tests for managed external frontend installation and refresh."""

from __future__ import annotations

import importlib
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

manager = importlib.import_module("frontend_external_manager")


class FakeRunner:
    def __init__(self, returncode: int = 0, output: str = "ok") -> None:
        self.returncode = returncode
        self.output = output
        self.calls: list[tuple[list[str], Path, int]] = []

    def __call__(self, args: list[str], cwd: Path, timeout: int) -> manager.CommandResult:
        self.calls.append((args, cwd, timeout))
        return manager.CommandResult(self.returncode, self.output, "")


class FrontendExternalManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.product = Path(self.temp.name) / "product"
        self.workspace = self.product / ".loop-engineer"
        self.workspace.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_ui_ux_pro_max_uses_latest_npm_cli_for_all_harnesses(self) -> None:
        runner = FakeRunner()

        result = manager.maintain_pack("ui-ux-pro-max", self.workspace, runner=runner)

        self.assertTrue(result.ok)
        args, cwd, _ = runner.calls[0]
        self.assertEqual(
            [
                manager.npx_command(),
                "--yes",
                "ui-ux-pro-max-cli@latest",
                "init",
                "--ai",
                "all",
                "--force",
            ],
            args,
        )
        self.assertEqual(self.product.resolve(), cwd)

    def test_taste_reinstalls_scoped_skill_for_all_harnesses_on_every_use(self) -> None:
        runner = FakeRunner()

        manager.maintain_pack("taste-skill", self.workspace, runner=runner)

        args, _, _ = runner.calls[0]
        self.assertEqual(manager.npx_command(), args[0])
        self.assertIn("skills@latest", args)
        self.assertEqual("*", args[args.index("--agent") + 1])
        self.assertIn("--copy", args)
        self.assertIn("--yes", args)
        self.assertEqual("design-taste-frontend", args[args.index("--skill") + 1])

    def test_threeui_uses_latest_exact_npm_dependency_on_every_use(self) -> None:
        (self.product / "package.json").write_text("{}\n", encoding="utf-8")
        runner = FakeRunner()

        result = manager.maintain_pack("threeui", self.workspace, runner=runner)

        self.assertTrue(result.ok)
        args, cwd, _ = runner.calls[0]
        self.assertEqual(
            [
                manager.npm_command(),
                "install",
                "@designcodeio/threeui@latest",
                "--save-exact",
            ],
            args,
        )
        self.assertEqual(self.product.resolve(), cwd)

    def test_threeui_fails_closed_without_product_package_json(self) -> None:
        runner = FakeRunner()

        result = manager.maintain_pack("threeui", self.workspace, runner=runner)

        self.assertFalse(result.ok)
        self.assertEqual("not-applicable", result.status)
        self.assertEqual([], runner.calls)

    def test_awesome_design_md_clones_then_pulls_managed_checkout(self) -> None:
        runner = FakeRunner()

        first = manager.maintain_pack("awesome-design-md", self.workspace, runner=runner)

        self.assertTrue(first.ok)
        clone_args, _, _ = runner.calls[0]
        self.assertEqual(["git", "clone", "--depth", "1"], clone_args[:4])
        checkout = manager.awesome_checkout(self.workspace)
        (checkout / ".git").mkdir(parents=True)

        second_runner = FakeRunner()
        second = manager.maintain_pack(
            "awesome-design-md", self.workspace, runner=second_runner
        )

        self.assertTrue(second.ok)
        pull_args, _, _ = second_runner.calls[0]
        self.assertEqual(["git", "-C", str(checkout), "pull", "--ff-only"], pull_args)

    def test_command_failure_is_reported_without_claiming_pack_is_current(self) -> None:
        runner = FakeRunner(returncode=1, output="failed")

        result = manager.maintain_pack("taste-skill", self.workspace, runner=runner)

        self.assertFalse(result.ok)
        self.assertEqual("update-failed", result.status)

    def test_global_data_without_product_root_does_not_install(self) -> None:
        global_data = Path.home() / ".loop-engineer" / "data"
        runner = FakeRunner()

        result = manager.maintain_pack("taste-skill", global_data, runner=runner)

        self.assertFalse(result.ok)
        self.assertEqual("no-product-root", result.status)
        self.assertEqual([], runner.calls)


if __name__ == "__main__":
    unittest.main(verbosity=2)
