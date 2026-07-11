"""Tests for the app/data split (global) and .loop-engineer/ nesting (local),
plus the legacy-layout migration. Stdlib unittest, no live network.

Run: python scripts/test_workspace_layout.py
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

import loop_home
import migrate_legacy_layout as mll
import workspace_resolver as wr


class LoopHomeSandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="loop-layout-test-"))
        self._prev = os.environ.get("LOOP_ENGINEER_HOME")
        os.environ["LOOP_ENGINEER_HOME"] = str(self.tmp)

    def tearDown(self) -> None:
        if self._prev is None:
            os.environ.pop("LOOP_ENGINEER_HOME", None)
        else:
            os.environ["LOOP_ENGINEER_HOME"] = self._prev
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestLoopHome(LoopHomeSandbox):
    def test_data_home_is_sibling_of_app(self) -> None:
        self.assertEqual(loop_home.data_home(), self.tmp / "data")
        self.assertEqual(loop_home.app_path(), self.tmp / "app")
        self.assertNotEqual(loop_home.data_home(), loop_home.app_path())

    def test_global_data_home_matches_data_home(self) -> None:
        self.assertEqual(loop_home.global_data_home(), loop_home.data_home())

    def test_registry_path_lives_under_data(self) -> None:
        self.assertEqual(
            loop_home.registry_path(), self.tmp / "data" / "registry" / "workspaces.json"
        )

    def test_ensure_loop_home_creates_app_bin_data(self) -> None:
        loop_home.ensure_loop_home()
        self.assertTrue((self.tmp / "app").is_dir())
        self.assertTrue((self.tmp / "bin").is_dir())
        self.assertTrue((self.tmp / "data").is_dir())
        self.assertTrue((self.tmp / "data" / "registry").is_dir())


class TestLocalDataDir(unittest.TestCase):
    def test_appends_dot_loop_engineer(self) -> None:
        product = Path("/tmp/my-product")
        self.assertEqual(wr.local_data_dir(product), product / ".loop-engineer")


class TestFindLocalWorkspace(LoopHomeSandbox):
    def setUp(self) -> None:
        super().setUp()
        self.product = self.tmp.parent / f"product-{os.getpid()}-{id(self)}"
        self.product.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.product, ignore_errors=True)
        super().tearDown()

    def test_no_data_dir_returns_none(self) -> None:
        self.assertIsNone(wr.find_local_workspace(self.product))

    def test_finds_nested_data_dir_with_markers(self) -> None:
        nested = self.product / ".loop-engineer" / "memories"
        nested.mkdir(parents=True)
        (nested / "MEMORY.md").write_text("# mem", encoding="utf-8")

        found = wr.find_local_workspace(self.product)
        self.assertEqual(found, self.product / ".loop-engineer")

    def test_finds_from_nested_subdirectory(self) -> None:
        nested = self.product / ".loop-engineer" / "memories"
        nested.mkdir(parents=True)
        (nested / "MEMORY.md").write_text("# mem", encoding="utf-8")
        deep = self.product / "src" / "components"
        deep.mkdir(parents=True)

        found = wr.find_local_workspace(deep)
        self.assertEqual(found, self.product / ".loop-engineer")

    def test_flat_legacy_markers_not_detected_as_new_style(self) -> None:
        """Old flat layout (no .loop-engineer/ subfolder) should NOT resolve
        as a valid new-style local workspace - that's the migration's job."""
        flat = self.product / "memories"
        flat.mkdir(parents=True)
        (flat / "MEMORY.md").write_text("# mem", encoding="utf-8")

        self.assertIsNone(wr.find_local_workspace(self.product))


class TestResolveEffectiveWorkspace(LoopHomeSandbox):
    def setUp(self) -> None:
        super().setUp()
        self.product = self.tmp.parent / f"product-{os.getpid()}-{id(self)}"
        self.product.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.product, ignore_errors=True)
        super().tearDown()

    def test_explicit_global_home_root_redirects_to_data(self) -> None:
        path, mode = wr.resolve_effective_workspace(str(self.tmp))
        self.assertEqual(mode, "global")
        self.assertEqual(path, self.tmp / "data")

    def test_explicit_global_data_dir_stays_global(self) -> None:
        path, mode = wr.resolve_effective_workspace(str(self.tmp / "data"))
        self.assertEqual(mode, "global")
        self.assertEqual(path, self.tmp / "data")

    def test_explicit_raw_product_folder_appends_dot_loop_engineer(self) -> None:
        path, mode = wr.resolve_effective_workspace(str(self.product))
        self.assertEqual(mode, "local")
        self.assertEqual(path, self.product / ".loop-engineer")

    def test_explicit_already_nested_path_not_double_appended(self) -> None:
        nested = str(self.product / ".loop-engineer")
        path, mode = wr.resolve_effective_workspace(nested)
        self.assertEqual(mode, "local")
        self.assertEqual(path, self.product / ".loop-engineer")


class TestMigrateLegacyLayout(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="loop-migrate-legacy-test-"))
        self.home = self.tmp / "home"
        self.product = self.tmp / "product"
        self.home.mkdir()
        self.product.mkdir()
        self._prev = os.environ.get("LOOP_ENGINEER_HOME")
        os.environ["LOOP_ENGINEER_HOME"] = str(self.home)

    def tearDown(self) -> None:
        if self._prev is None:
            os.environ.pop("LOOP_ENGINEER_HOME", None)
        else:
            os.environ["LOOP_ENGINEER_HOME"] = self._prev
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _seed_legacy_global(self) -> None:
        (self.home / "memories").mkdir()
        (self.home / "memories" / "MEMORY.md").write_text("# old", encoding="utf-8")
        (self.home / "main_plan.md").write_text("plan", encoding="utf-8")
        (self.home / "state.db").write_text("db", encoding="utf-8")

    def _seed_legacy_local(self) -> None:
        (self.product / "memories").mkdir()
        (self.product / "memories" / "MEMORY.md").write_text("# old local", encoding="utf-8")
        (self.product / "main_plan.md").write_text("plan", encoding="utf-8")
        (self.product / "src").mkdir()
        (self.product / "src" / "index.js").write_text("code", encoding="utf-8")

    def test_is_legacy_global_detects_flat_layout(self) -> None:
        self.assertFalse(mll.is_legacy_global(self.home))
        self._seed_legacy_global()
        self.assertTrue(mll.is_legacy_global(self.home))

    def test_is_legacy_global_false_once_data_dir_exists(self) -> None:
        self._seed_legacy_global()
        (self.home / "data").mkdir()
        self.assertFalse(mll.is_legacy_global(self.home))

    def test_migrate_global_dry_run_does_not_move(self) -> None:
        self._seed_legacy_global()
        mll.migrate_global(apply=False)
        self.assertTrue((self.home / "memories").exists())
        self.assertFalse((self.home / "data").exists())

    def test_migrate_global_apply_moves_into_data(self) -> None:
        self._seed_legacy_global()
        mll.migrate_global(apply=True)
        self.assertFalse((self.home / "memories").exists())
        self.assertTrue((self.home / "data" / "memories" / "MEMORY.md").exists())
        self.assertTrue((self.home / "data" / "main_plan.md").exists())
        self.assertTrue((self.home / "data" / "state.db").exists())

    def test_migrate_local_apply_moves_and_protects_product_code(self) -> None:
        self._seed_legacy_local()
        mll.migrate_local(self.product, apply=True)
        self.assertFalse((self.product / "memories").exists())
        self.assertTrue((self.product / ".loop-engineer" / "memories" / "MEMORY.md").exists())
        # Product's own code must be completely untouched.
        self.assertTrue((self.product / "src" / "index.js").exists())
        self.assertEqual((self.product / "src" / "index.js").read_text(encoding="utf-8"), "code")

    def test_migrate_local_does_not_bulk_move_docs_or_skills(self) -> None:
        self._seed_legacy_local()
        (self.product / "docs").mkdir()
        (self.product / "docs" / "my-own-readme.md").write_text("mine", encoding="utf-8")
        mll.migrate_local(self.product, apply=True)
        # docs/ is flagged, not moved - the user's own file must stay put.
        self.assertTrue((self.product / "docs" / "my-own-readme.md").exists())

    def test_migrate_skips_when_target_exists(self) -> None:
        self._seed_legacy_global()
        (self.home / "data").mkdir()
        (self.home / "data" / "memories").mkdir()
        results = mll.migrate_global(apply=True)
        self.assertTrue(any("nothing to do" in r for r in results))
        # Original untouched since is_legacy_global returns False once data/ exists.
        self.assertTrue((self.home / "memories").exists())


class TestMainPlanResolver(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="loop-mainplan-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_prefers_canonical_plan_location(self) -> None:
        from memory_paths import main_plan_file

        (self.tmp / "plan").mkdir()
        (self.tmp / "plan" / "main_plan.md").write_text("canonical", encoding="utf-8")
        (self.tmp / "main_plan.md").write_text("legacy", encoding="utf-8")
        self.assertEqual(main_plan_file(self.tmp), self.tmp / "plan" / "main_plan.md")

    def test_falls_back_to_legacy_root(self) -> None:
        from memory_paths import main_plan_file

        (self.tmp / "main_plan.md").write_text("legacy", encoding="utf-8")
        self.assertEqual(main_plan_file(self.tmp), self.tmp / "main_plan.md")

    def test_defaults_to_canonical_when_neither_exists(self) -> None:
        from memory_paths import main_plan_file

        self.assertEqual(main_plan_file(self.tmp), self.tmp / "plan" / "main_plan.md")


class TestMigration008(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="loop-mig008-test-"))
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "mig008", Path(__file__).resolve().parents[1] / "migrations" / "008_organize_memory_layout.py"
        )
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _seed(self, ws, rel, src):
        return None

    def test_moves_main_plan_into_plan_dir(self) -> None:
        (self.tmp / "main_plan.md").write_text("# Plan", encoding="utf-8")
        self.mod.apply(self.tmp, self._seed)
        self.assertFalse((self.tmp / "main_plan.md").exists())
        self.assertEqual((self.tmp / "plan" / "main_plan.md").read_text(encoding="utf-8"), "# Plan")

    def test_removes_duplicate_root_memory(self) -> None:
        (self.tmp / "memories").mkdir()
        (self.tmp / "memories" / "MEMORY.md").write_text("# Mem\n", encoding="utf-8")
        (self.tmp / "MEMORY.md").write_text("# Mem\n", encoding="utf-8")
        self.mod.apply(self.tmp, self._seed)
        self.assertFalse((self.tmp / "MEMORY.md").exists())
        self.assertTrue((self.tmp / "memories" / "MEMORY.md").exists())

    def test_preserves_diverged_root_memory(self) -> None:
        (self.tmp / "memories").mkdir()
        (self.tmp / "memories" / "MEMORY.md").write_text("# canonical", encoding="utf-8")
        (self.tmp / "MEMORY.md").write_text("# diverged edits", encoding="utf-8")
        self.mod.apply(self.tmp, self._seed)
        self.assertFalse((self.tmp / "MEMORY.md").exists())
        backup = self.tmp / "memories" / "MEMORY.root-legacy.md"
        self.assertEqual(backup.read_text(encoding="utf-8"), "# diverged edits")
        self.assertEqual((self.tmp / "memories" / "MEMORY.md").read_text(encoding="utf-8"), "# canonical")

    def test_moves_root_memory_when_no_canonical(self) -> None:
        (self.tmp / "MEMORY.md").write_text("# only copy", encoding="utf-8")
        self.mod.apply(self.tmp, self._seed)
        self.assertEqual((self.tmp / "memories" / "MEMORY.md").read_text(encoding="utf-8"), "# only copy")

    def test_moves_startup_memory(self) -> None:
        (self.tmp / "STARTUP_MEMORY.md").write_text("legacy", encoding="utf-8")
        self.mod.apply(self.tmp, self._seed)
        self.assertFalse((self.tmp / "STARTUP_MEMORY.md").exists())
        self.assertTrue((self.tmp / "memories" / "STARTUP_MEMORY.md").exists())

    def test_idempotent_on_organized_workspace(self) -> None:
        (self.tmp / "plan").mkdir()
        (self.tmp / "plan" / "main_plan.md").write_text("# Plan", encoding="utf-8")
        results = self.mod.apply(self.tmp, self._seed)
        self.assertIn("memory layout already organized", results)


if __name__ == "__main__":
    unittest.main()
