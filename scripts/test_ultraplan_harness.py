"""Ultraplan selection stays inside the owning planning scope."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ultraplan_harness as ultra  # noqa: E402


PRODUCT_MAP = """# Product Map

| ID | Step file | Type | Title | Scope | Depends on | Status |
|----|---|---|---|---|---|---|
| 01 | step_01 | sub-product | Denial Recovery | plan/products/denial-recovery | | Built |
| 02 | step_02 | program | Revenue Activation | | 01 | Active |
| 19 | step_19 | platform capability | Identity and Access Platform | | | Active |
"""


class UltraplanSelection(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="loop-ultraplan-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.ws = self.root / ".loop-engineer"
        (self.ws / "plan").mkdir(parents=True)
        (self.ws / "plan" / "PRODUCT_MAP.md").write_text(PRODUCT_MAP, encoding="utf-8")

    def test_root_tracker_skips_rows_owned_by_a_sub_product_scope(self) -> None:
        rows = ultra.root_ultraplan_modules(self.ws)
        self.assertEqual(["02", "19"], [row["id"] for row in rows])

    def test_an_explicit_step_overrides_the_default_next_step(self) -> None:
        selected = ultra.find_next_incomplete(self.ws, target="19")
        self.assertEqual({"id": "19", "title": "Identity and Access Platform"}, selected)

    def test_an_explicit_title_selects_the_existing_step(self) -> None:
        selected = ultra.find_next_incomplete(self.ws, target="Identity and Access Platform")
        self.assertEqual("19", selected["id"])

    def test_a_delegated_step_cannot_be_selected_from_the_root_tracker(self) -> None:
        self.assertIsNone(ultra.find_next_incomplete(self.ws, target="01"))

    def test_an_all_delegated_map_does_not_fall_back_to_root_step_files(self) -> None:
        (self.ws / "plan" / "PRODUCT_MAP.md").write_text(
            """# Product Map

| ID | Step file | Type | Title | Scope | Status |
|----|---|---|---|---|---|
| 01 | step_01 | sub-product | Denial Recovery | plan/products/denial-recovery | Built |
""",
            encoding="utf-8",
        )
        (self.ws / "plan" / "step_01_denial-recovery.md").write_text("# delegated", encoding="utf-8")

        self.assertIsNone(ultra.find_next_incomplete(self.ws))
        status = ultra.update_ultraplan_status(self.ws).read_text(encoding="utf-8")
        self.assertNotIn("denial recovery", status.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
