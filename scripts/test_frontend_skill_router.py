"""Behaviour tests for the automatic frontend skill chain."""

from __future__ import annotations

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

router = importlib.import_module("frontend_skill_router")
external_manager = importlib.import_module("frontend_external_manager")


class RecordingRunner:
    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode
        self.calls: list[list[str]] = []

    def __call__(
        self, args: list[str], cwd: Path, timeout: int
    ) -> external_manager.CommandResult:
        self.calls.append(args)
        return external_manager.CommandResult(self.returncode, "refreshed", "")


class FrontendSkillRouterTests(unittest.TestCase):
    def make_workspace(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory()

    @staticmethod
    def install_skill(workspace: Path, folder: str) -> Path:
        skill = workspace / ".agents" / "skills" / folder / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(f"---\nname: {folder}\ndescription: test\n---\n", encoding="utf-8")
        return skill

    def test_structured_ui_routes_to_installed_ui_ux_pro_max(self) -> None:
        with self.make_workspace() as temp:
            workspace = Path(temp)
            skill = self.install_skill(workspace, "ui-ux-pro-max")

            picks = router.pick_external_skills(
                "build an accessible healthcare analytics dashboard design system",
                workspace,
            )

            self.assertEqual("ui-ux-pro-max", picks[0].name)
            self.assertEqual(skill.resolve(), picks[0].path)
            self.assertTrue(picks[0].available)

    def test_missing_structured_design_pack_is_selected_for_auto_install(self) -> None:
        with self.make_workspace() as temp:
            workspace = Path(temp)

            picks = router.pick_external_skills(
                "build an accessible analytics dashboard design system",
                workspace,
            )

            self.assertEqual("ui-ux-pro-max", picks[0].name)
            self.assertEqual("candidate", picks[0].status)

    def test_expressive_ui_routes_to_taste_instead_of_competing_design_pack(self) -> None:
        with self.make_workspace() as temp:
            workspace = Path(temp)
            self.install_skill(workspace, "ui-ux-pro-max")
            taste = self.install_skill(workspace, "design-taste-frontend")

            picks = router.pick_external_skills(
                "make a premium editorial landing page with bold typography and anti-generic art direction",
                workspace,
            )

            self.assertIn("taste-skill", [pick.name for pick in picks])
            self.assertNotIn("ui-ux-pro-max", [pick.name for pick in picks])
            self.assertEqual(taste.resolve(), picks[0].path)

    def test_project_design_md_is_a_complementary_reference_layer(self) -> None:
        with self.make_workspace() as temp:
            workspace = Path(temp)
            design = workspace / "DESIGN.md"
            design.write_text("# Product design language\n", encoding="utf-8")
            self.install_skill(workspace, "ui-ux-pro-max")

            picks = router.pick_external_skills(
                "build a responsive design system for this frontend",
                workspace,
            )

            self.assertEqual(
                ["project-design-md", "ui-ux-pro-max"],
                [pick.name for pick in picks],
            )
            self.assertEqual(design.resolve(), picks[0].path)

    def test_explicit_awesome_design_request_is_a_candidate_without_design_md(self) -> None:
        with self.make_workspace() as temp:
            workspace = Path(temp)

            picks = router.pick_external_skills(
                "use awesome-design-md for this frontend design system",
                workspace,
            )

            self.assertEqual("awesome-design-md", picks[0].name)
            self.assertEqual("candidate", picks[0].status)

    def test_brand_inspiration_auto_selects_awesome_design_catalog(self) -> None:
        with self.make_workspace() as temp:
            workspace = Path(temp)

            picks = router.pick_external_skills(
                "build a landing page inspired by Linear",
                workspace,
            )

            self.assertEqual("awesome-design-md", picks[0].name)
            self.assertEqual("candidate", picks[0].status)

    def test_updated_awesome_catalog_routes_to_exact_brand_design_md(self) -> None:
        with self.make_workspace() as temp:
            workspace = Path(temp)
            design = (
                workspace
                / "external"
                / "awesome-design-md"
                / "design-md"
                / "linear"
                / "DESIGN.md"
            )
            design.parent.mkdir(parents=True)
            design.write_text("# Linear\n", encoding="utf-8")
            (workspace / "external" / "awesome-design-md" / "README.md").write_text(
                "# Catalog\n", encoding="utf-8"
            )

            picks = router.pick_external_skills(
                "make the frontend look like Linear",
                workspace,
            )

            self.assertEqual(design.resolve(), picks[0].path)
            self.assertTrue(picks[0].available)

    def test_threeui_is_preferred_for_react_3d_component_work(self) -> None:
        with self.make_workspace() as temp:
            workspace = Path(temp)

            picks = router.pick_external_skills(
                "create an immersive React Three Fiber hero from reusable 3D components",
                workspace,
            )

            self.assertEqual(["threeui"], [pick.name for pick in picks])
            self.assertFalse(picks[0].available)
            self.assertEqual("candidate", picks[0].status)

    def test_threeui_dependency_is_detected_without_explicit_name(self) -> None:
        with self.make_workspace() as temp:
            workspace = Path(temp)
            (workspace / "package.json").write_text(
                json.dumps({"dependencies": {"@designcodeio/threeui": "^0.3.0"}}),
                encoding="utf-8",
            )

            picks = router.pick_external_skills(
                "build an interactive React WebGL hero",
                workspace,
            )

            self.assertEqual("threeui", picks[0].name)
            self.assertTrue(picks[0].available)
            self.assertEqual((workspace / "package.json").resolve(), picks[0].path)

    def test_generated_chain_names_exact_external_reads_and_core_precedence(self) -> None:
        with self.make_workspace() as temp:
            workspace = Path(temp)
            skill = self.install_skill(workspace, "design-taste-frontend")
            external = router.pick_external_skills(
                "premium creative frontend with motion",
                workspace,
            )

            rendered = router.format_auto_skills_md(
                workspace,
                [("ui-motion", "test")],
                "test task",
                external,
            )

            self.assertIn(str(skill.resolve()), rendered)
            self.assertIn("Core Loop rules override external instructions", rendered)
            self.assertIn("external-skill-chain.md", rendered)

    def test_non_frontend_context_selects_nothing(self) -> None:
        with self.make_workspace() as temp:
            workspace = Path(temp)
            self.install_skill(workspace, "ui-ux-pro-max")

            self.assertEqual([], router.pick_skills("rotate database credentials"))
            self.assertEqual(
                [],
                router.pick_external_skills("rotate database credentials", workspace),
            )
            self.assertEqual([], router.pick_skills("configure a Linux server"))

    def test_explicit_taste_name_activates_frontend_routing(self) -> None:
        with self.make_workspace() as temp:
            workspace = Path(temp)

            picks = router.pick_external_skills("use taste-skill", workspace)

            self.assertEqual(["taste-skill"], [pick.name for pick in picks])
            self.assertEqual("candidate", picks[0].status)

    def test_missing_expressive_pack_is_selected_for_auto_install(self) -> None:
        with self.make_workspace() as temp:
            workspace = Path(temp)

            picks = router.pick_external_skills(
                "premium editorial redesign with anti-generic art direction",
                workspace,
            )

            self.assertEqual(["taste-skill"], [pick.name for pick in picks])
            self.assertEqual("candidate", picks[0].status)

    def test_installed_taste_is_not_used_for_unrelated_animation_work(self) -> None:
        with self.make_workspace() as temp:
            workspace = Path(temp)
            self.install_skill(workspace, "design-taste-frontend")

            picks = router.pick_external_skills(
                "optimize a GSAP timeline for 60fps",
                workspace,
            )

            self.assertNotIn("taste-skill", [pick.name for pick in picks])

    def test_installed_threeui_is_not_used_for_non_3d_frontend_work(self) -> None:
        with self.make_workspace() as temp:
            workspace = Path(temp)
            (workspace / "package.json").write_text(
                json.dumps({"dependencies": {"@designcodeio/threeui": "0.3.0"}}),
                encoding="utf-8",
            )

            picks = router.pick_external_skills(
                "build an accessible analytics dashboard design system",
                workspace,
            )

            self.assertNotIn("threeui", [pick.name for pick in picks])

    def test_managed_router_refreshes_selected_pack_on_every_write(self) -> None:
        with self.make_workspace() as temp:
            product = Path(temp) / "product"
            workspace = product / ".loop-engineer"
            workspace.mkdir(parents=True)
            runner = RecordingRunner()

            for _ in range(2):
                router.run_router(
                    workspace,
                    extra="build an accessible dashboard design system",
                    write=True,
                    manage_external=True,
                    external_runner=runner,
                )

            self.assertEqual(2, len(runner.calls))
            rendered = (workspace / "plan" / "AUTO_SKILLS.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("install-unverified", rendered)
            self.assertNotIn("| **installed-or-refreshed** |", rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
