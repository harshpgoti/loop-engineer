"""A generated file must know when it stopped being true.

The last class of tests here is a Loop Engineer build fuzz:
mutate a *declared* input and assert the view flips stale; mutate an *undeclared* one
and assert it stays clean. Hashing fails silently when the declared input list is
wrong - unlike timestamps, which fail loudly - so this is the guard that matters.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import freshness  # noqa: E402


class Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = Path(tempfile.mkdtemp(prefix="loop-fresh-"))
        (self.ws / "plan").mkdir(parents=True, exist_ok=True)
        (self.ws / "TASKS.yml").write_text("tasks:\n  - id: TASK-001\n    status: open\n", encoding="utf-8")
        (self.ws / "GATES.yml").write_text("gates:\n  G-ONE:\n    status: blocked\n", encoding="utf-8")
        (self.ws / "DOUBTS.md").write_text("# Doubts\n\n### DQ-001: Open\n- **Status:** open\n", encoding="utf-8")
        self.view = self.ws / "plan" / "BUILD_CONTEXT.md"
        self.view.write_text("# Build Context\n\nActive task: TASK-001\n", encoding="utf-8")
        self.sources = [self.ws / "TASKS.yml", self.ws / "GATES.yml"]

    def tearDown(self) -> None:
        shutil.rmtree(self.ws, ignore_errors=True)

    def stamp(self, *, version: int = 1) -> None:
        freshness.stamp(self.view, self.sources, generator="build-context", version=version, workspace=self.ws)

    def check(self, *, version: int | None = None) -> dict:
        return freshness.check(self.view, workspace=self.ws, version=version)


class Basics(Sandbox):
    def test_a_freshly_stamped_view_is_fresh(self) -> None:
        self.stamp()
        self.assertTrue(self.check()["fresh"])

    def test_an_unstamped_view_is_not_trusted(self) -> None:
        self.assertFalse(self.check()["fresh"])
        self.assertIn("no provenance stamp", self.check()["reason"])

    def test_the_body_survives_stamping(self) -> None:
        self.stamp()
        self.assertIn("Active task: TASK-001", self.view.read_text(encoding="utf-8"))

    def test_restamping_is_stable(self) -> None:
        self.stamp()
        once = self.view.read_text(encoding="utf-8")
        self.stamp()
        self.assertEqual(once, self.view.read_text(encoding="utf-8"))

    def test_a_view_is_never_its_own_input(self) -> None:
        """dbt's self-overwrite bug: an index that feeds itself never sees a change."""
        self.stamp()
        first = freshness.read_stamp(self.view)["output_hash"]
        self.stamp()
        self.assertEqual(first, freshness.read_stamp(self.view)["output_hash"])


class Invalidation(Sandbox):
    def test_a_changed_input_makes_it_stale(self) -> None:
        self.stamp()
        (self.ws / "TASKS.yml").write_text("tasks:\n  - id: TASK-001\n    status: done\n", encoding="utf-8")
        result = self.check()
        self.assertFalse(result["fresh"])
        self.assertEqual(["TASKS.yml"], [c["path"] for c in result["changed"]])

    def test_it_names_which_input_moved(self) -> None:
        """So a caller can regenerate one section, not the whole file."""
        self.stamp()
        (self.ws / "GATES.yml").write_text("gates:\n  G-ONE:\n    status: passed\n", encoding="utf-8")
        self.assertIn("GATES.yml", self.check()["reason"])

    def test_a_removed_input_is_detected(self) -> None:
        """The case no timestamp scheme can see: survivors are all still older."""
        self.stamp()
        (self.ws / "GATES.yml").unlink()
        result = self.check()
        self.assertFalse(result["fresh"])
        self.assertTrue(result["changed"][0]["gone"])

    def test_a_hand_edited_view_is_reported_not_clobbered(self) -> None:
        self.stamp()
        body = self.view.read_text(encoding="utf-8")
        self.view.write_text(body + "\n\nA human added this line.\n", encoding="utf-8")
        result = self.check()
        self.assertFalse(result["fresh"])
        self.assertTrue(result.get("edited"))

    def test_a_generator_change_invalidates_everything_it_made(self) -> None:
        """Make's most famous defect: edit the template, views stay wrong-but-clean."""
        self.stamp(version=1)
        self.assertTrue(self.check(version=1)["fresh"])
        self.assertFalse(self.check(version=2)["fresh"])
        self.assertIn("generator changed", self.check(version=2)["reason"])


class NoiseImmunity(Sandbox):
    def test_line_ending_changes_do_not_make_it_stale(self) -> None:
        """`core.autocrlf` on a fresh Windows clone would otherwise flip everything."""
        self.stamp()
        original = (self.ws / "TASKS.yml").read_text(encoding="utf-8")
        (self.ws / "TASKS.yml").write_bytes(original.replace("\n", "\r\n").encode("utf-8"))
        self.assertTrue(self.check()["fresh"])

    def test_a_redated_header_does_not_make_it_stale(self) -> None:
        """Volatile fields change without changing meaning - dbt ignores tags/meta too."""
        (self.ws / "TASKS.yml").write_text(
            "updated: 2026-08-01\ntasks:\n  - id: TASK-001\n    status: open\n", encoding="utf-8"
        )
        self.stamp()
        (self.ws / "TASKS.yml").write_text(
            "updated: 2026-08-20\ntasks:\n  - id: TASK-001\n    status: open\n", encoding="utf-8"
        )
        self.assertTrue(self.check()["fresh"])

    def test_trailing_whitespace_does_not_make_it_stale(self) -> None:
        self.stamp()
        original = (self.ws / "TASKS.yml").read_text(encoding="utf-8")
        (self.ws / "TASKS.yml").write_text(original.replace("open\n", "open   \n"), encoding="utf-8")
        self.assertTrue(self.check()["fresh"])


class BuildFuzz(Sandbox):
    """Mutate one input at a time and assert the staleness verdict is correct.

    Hand-maintained dependency lists are reliably wrong, and with content
    hashing a missing declaration fails silent and permanent.
    """

    def _mutate(self, path: Path) -> None:
        path.write_text(path.read_text(encoding="utf-8") + "\n# sentinel\n", encoding="utf-8")

    def test_every_declared_input_can_invalidate(self) -> None:
        for name in [s.name for s in self.sources]:
            with self.subTest(source=name):
                self.setUp()  # rebuilds the workspace, so re-resolve the path inside it
                self.stamp()
                self.assertTrue(self.check()["fresh"])
                self._mutate(self.ws / name)
                self.assertFalse(self.check()["fresh"], f"{name} is declared but cannot invalidate")

    def test_an_undeclared_input_does_not_invalidate(self) -> None:
        self.stamp()
        self._mutate(self.ws / "DOUBTS.md")  # real input of BUILD_CONTEXT, not declared here
        self.assertTrue(self.check()["fresh"], "only declared inputs may drive staleness")

    def test_the_fuzz_catches_a_missing_declaration(self) -> None:
        """The failure this whole class exists to detect, demonstrated deliberately."""
        undeclared = self.ws / "DOUBTS.md"
        self.stamp()  # sources deliberately omit DOUBTS.md
        self._mutate(undeclared)
        self.assertTrue(self.check()["fresh"])

        freshness.stamp(
            self.view, self.sources + [undeclared], generator="build-context", version=1, workspace=self.ws
        )
        self._mutate(undeclared)
        self.assertFalse(self.check()["fresh"], "once declared, it must invalidate")


class Sweep(Sandbox):
    def test_stale_views_finds_only_stamped_files(self) -> None:
        (self.ws / "plan" / "hand-written.md").write_text("# Notes\n\nNot generated.\n", encoding="utf-8")
        self.stamp()
        (self.ws / "TASKS.yml").write_text("tasks: []\n", encoding="utf-8")
        stale = freshness.stale_views(self.ws)
        self.assertEqual(["plan/BUILD_CONTEXT.md"], [s["view"] for s in stale])

    def test_nothing_stale_when_sources_are_untouched(self) -> None:
        self.stamp()
        self.assertEqual([], freshness.stale_views(self.ws))


if __name__ == "__main__":
    unittest.main(verbosity=2)
