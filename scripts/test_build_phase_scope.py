"""The build router must follow the selected sub-product, not the root folder.

Both cases here were found on a real platform whose three sub-products had all been
absorbed: the root folder holds no code and no product tasks, so a router that only
looks there gives the wrong answer twice over.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_phase  # noqa: E402
import scope_paths as sp  # noqa: E402


class UnifiedPlatform(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        self.product = self.root / "Platform"
        self.ws = self.product / ".loop-engineer"
        (self.ws / "plan").mkdir(parents=True)
        (self.ws / "TASKS.yml").write_text(
            "tasks:\n  - id: TASK-M-001\n    title: platform CI\n    status: todo\n", encoding="utf-8"
        )

        # auth is built; portal is not
        self.auth = sp.create_scope(self.ws, "auth", name="Auth", map_id="01", code_dir="services/auth")
        (self.product / "services" / "auth" / "src").mkdir(parents=True)
        (self.product / "services" / "auth" / "package.json").write_text("{}", encoding="utf-8")
        self.auth.tasks_file.write_text(
            "tasks:\n  - id: AUTH-TASK-001\n    title: sessions\n    status: todo\n", encoding="utf-8"
        )

        self.portal = sp.create_scope(self.ws, "portal", name="Portal", map_id="02", code_dir="apps/portal")
        (self.product / "apps" / "portal").mkdir(parents=True)

    def phase(self) -> dict:
        return build_phase.compute_build_phase(self.ws)


class SourceTree(UnifiedPlatform):
    def test_a_built_scope_is_not_told_to_scaffold(self) -> None:
        """The root folder holds no code; the scope's does."""
        sp.set_active(self.ws, "auth", session="s1")
        self.assertNotEqual(self.phase()["phase"], "scaffold")

    def test_an_unbuilt_scope_is_told_to_scaffold_even_when_a_sibling_is_built(self) -> None:
        sp.set_active(self.ws, "portal", session="s1")
        self.assertEqual(self.phase()["phase"], "scaffold")

    def test_with_no_scope_selected_an_existing_sub_product_still_counts_as_built(self) -> None:
        """Scaffolding at platform level would be scaffolding over existing work."""
        sp.clear_active(self.ws)
        self.assertNotEqual(self.phase()["phase"], "scaffold")

    def test_a_workspace_with_no_scopes_is_unchanged(self) -> None:
        plain = self.root / "Plain" / ".loop-engineer"
        (plain / "plan").mkdir(parents=True)
        (plain / "TASKS.yml").write_text("tasks:\n  - id: T-1\n    status: todo\n", encoding="utf-8")
        self.assertEqual(build_phase.compute_build_phase(plain)["phase"], "scaffold")


class TaskSelection(UnifiedPlatform):
    def test_the_selected_scope_s_own_task_is_chosen(self) -> None:
        sp.set_active(self.ws, "auth", session="s1")
        self.assertEqual(self.phase()["task"], "AUTH-TASK-001")

    def test_platform_work_is_used_when_the_scope_has_nothing_open(self) -> None:
        self.auth.tasks_file.write_text(
            "tasks:\n  - id: AUTH-TASK-001\n    title: sessions\n    status: done\n", encoding="utf-8"
        )
        sp.set_active(self.ws, "auth", session="s1")
        self.assertEqual(self.phase()["task"], "TASK-M-001")

    def test_another_scope_s_task_is_never_chosen_for_this_scope(self) -> None:
        self.portal.tasks_file.write_text(
            "tasks:\n  - id: PORTAL-TASK-001\n    title: login\n    status: in_progress\n", encoding="utf-8"
        )
        sp.set_active(self.ws, "auth", session="s1")
        self.assertEqual(self.phase()["task"], "AUTH-TASK-001")
