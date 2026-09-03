"""Regression tests for the session-end MEMORY.md destruction bug.

Covers: header stacking, heading loss, section-sign injection into plain
markdown, oldest-kept trimming, boilerplate closeout spam, poisoned staged
replaces, sync-note spam, and the session-end CLI flag mismatch.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from memory_curator import (  # noqa: E402
    apply_report,
    normalize_header,
    propose_closeout_entries,
    propose_updates,
    trim_to_limit,
    uses_section_sign,
    validate_memory_output,
)
from memory_paths import ensure_memory_layout, memory_file  # noqa: E402
from pending_writes import (  # noqa: E402
    approve_pending,
    list_pending,
    reject_pending,
    stage_memory_write,
)
from session_lifecycle import session_end  # noqa: E402
from sync_loop_state import detect_drift, ensure_memory_timestamp  # noqa: E402

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "MEMORY.template.md"

HAND_MD = (
    "# Memory\n\n"
    "> warning banner stays\n\n"
    "Intro line.\n\n"
    "## Recent\n\n"
    "- 2026-09-04 entry one with enough detail to be real memory content here.\n"
    "- 2026-09-03 entry two with enough detail to be real memory content here.\n"
)


def make_workspace(files: dict) -> Path:
    tmp = Path(tempfile.mkdtemp()) / ".loop-engineer"
    tmp.mkdir(parents=True)
    ensure_memory_layout(tmp)
    for rel, text in files.items():
        path = tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp


def closeout(ws: Path, n: int = 3) -> str:
    for _ in range(n):
        apply_report(ws, propose_updates(ws))
    return memory_file(ws).read_text(encoding="utf-8")


class TemplatePreservation(unittest.TestCase):
    def test_template_survives_repeated_closeouts(self):
        ws = make_workspace(
            {
                "memories/MEMORY.md": TEMPLATE.read_text(encoding="utf-8"),
                "DECISIONS.md": "# D\n",
                "HANDOFF.md": "# H\n",
            }
        )
        out = closeout(ws, 3)
        for heading in ("## Current Mental State", "## What We Did", "## What Comes Next"):
            self.assertIn(heading, out, f"closeout dropped {heading}")
        self.assertEqual(1, out.count("# Memory"))
        self.assertNotIn("§", out)


class MarkdownDiaryPreservation(unittest.TestCase):
    def test_recent_heading_and_no_sign_injection(self):
        ws = make_workspace(
            {"memories/MEMORY.md": HAND_MD, "DECISIONS.md": "# D\n", "HANDOFF.md": "# H\n"}
        )
        out = closeout(ws, 2)
        self.assertIn("## Recent", out)
        self.assertIn("warning banner stays", out)
        self.assertNotIn("§", out)
        self.assertEqual(1, out.count("# Memory"))

    def test_closeout_appends_as_markdown_bullets(self):
        ws = make_workspace(
            {
                "memories/MEMORY.md": HAND_MD,
                "DECISIONS.md": "# D\n\n- Chose Postgres over DynamoDB for the billing ledger, needs transactions\n",
                "HANDOFF.md": "# H\n",
            }
        )
        out = closeout(ws, 1)
        self.assertIn("Postgres over DynamoDB", out)
        self.assertNotIn("§", out)

    def test_repeat_runs_do_not_duplicate(self):
        ws = make_workspace(
            {
                "memories/MEMORY.md": HAND_MD,
                "DECISIONS.md": "# D\n\n- Chose Postgres over DynamoDB for the billing ledger, needs transactions\n",
                "HANDOFF.md": "# H\n",
            }
        )
        first = closeout(ws, 1)
        after = closeout(ws, 3)
        self.assertEqual(first.count("Postgres over DynamoDB"), after.count("Postgres over DynamoDB"))

    def test_collapse_is_refused_not_written(self):
        big = "# Memory\n\n" + ("Meaningful project context line with real substance. " * 40) + "\n"
        ws = make_workspace({"memories/MEMORY.md": big})
        report = propose_updates(ws)
        report["memory_output"] = "# Memory\n\ntiny\n"
        actions = apply_report(ws, report)
        self.assertTrue(any("withheld" in a for a in actions))
        self.assertGreater(len(memory_file(ws).read_text(encoding="utf-8")), len(big) // 2)

    def test_inline_header_mentions_do_not_count(self):
        from memory_curator import _header_lines, validate_memory_output

        quoted = "# Memory\n\n> banner noting the `# Memory` header rule\n\nBody here.\n"
        self.assertEqual(1, _header_lines(quoted))
        self.assertEqual([], validate_memory_output(quoted, quoted + "\n- new entry with enough detail to be kept\n"))

    def test_over_budget_diary_is_preserved_with_suggestion(self):
        bullets = "".join(
            f"- 2026-01-{i:02d} diary entry with enough substance to count as real memory content here and a little more detail to fill the budget.\n"
            for i in range(1, 61)
        )
        big = "# Memory\n\nIntro.\n\n## Recent\n\n" + bullets
        self.assertGreater(len(big), 2200 * 2)
        ws = make_workspace({"memories/MEMORY.md": big, "DECISIONS.md": "# D\n", "HANDOFF.md": "# H\n"})
        report = propose_updates(ws)
        self.assertTrue(report["memory_trim_suggestion"], "over budget must come with a trim suggestion")
        out = closeout(ws, 1)
        self.assertIn("## Recent", out)
        # Nothing auto-deleted: oldest and newest entries both survive.
        self.assertIn("2026-01-01", out)
        self.assertIn("2026-01-60", out)
        self.assertGreater(len(out), len(big) * 0.95)


class HeaderIdempotency(unittest.TestCase):
    def test_stacked_headers_collapse(self):
        stacked = "# Memory\n\n# Memory\n\n# Memory\n\nReal content here.\n"
        self.assertEqual(1, normalize_header(stacked).count("# Memory"))
        self.assertIn("Real content here.", normalize_header(stacked))

    def test_join_never_stacks(self):
        ws = make_workspace(
            {"memories/MEMORY.md": "# Memory\n\n# Memory\n\nReal content here.\n"}
        )
        out = closeout(ws, 2)
        self.assertEqual(1, out.count("# Memory"))


class TrimDirection(unittest.TestCase):
    def test_sectioned_trim_keeps_newest(self):
        entries = ["intro"] + [f"entry {i:02d} " + "x" * 60 for i in range(20)]
        kept, dropped = trim_to_limit(entries, 500)
        self.assertIn("intro", kept)
        self.assertIn(entries[-1], kept, "newest entry must survive trimming")
        self.assertIn(entries[1], dropped, "oldest entries drop first")

    def test_validation_rejects_collapse(self):
        before = "# Memory\n\n" + "substance " * 200 + "\n"
        self.assertTrue(validate_memory_output(before, "# Memory\n\ntiny\n"))
        self.assertFalse(validate_memory_output(before, before + "\n- more\n"))


class ProposerQuality(unittest.TestCase):
    def test_boilerplate_is_never_proposed(self):
        ws = make_workspace(
            {
                "DECISIONS.md": "# D\n\n- Use `/plan` for Step 1.\n- Keep reusable logic in `skills/` and `commands/`.\n",
                "HANDOFF.md": "# H\n\n- Created reusable loop command contracts:\n- Waiting for the user to run `/plan-loop`.\n",
            }
        )
        proposals = propose_closeout_entries(ws, "some memory")
        self.assertEqual([], proposals)

    def test_short_and_warning_lines_skipped(self):
        ws = make_workspace(
            {
                "DECISIONS.md": "# D\n\n- Too short\n",
                "HANDOFF.md": "# H\n\n- WARNING do not approve anything\n",
            }
        )
        self.assertEqual([], propose_closeout_entries(ws, "some memory"))

    def test_triplicated_log_lines_propose_nothing(self):
        ws = make_workspace(
            {
                "DECISIONS.md": "# D\n",
                "HANDOFF.md": "# H\n\n- plan/PROD-GAP.md was updated. Ask the user to resolve human-required blockers listed there. Agent may continue with safe P0/P1 technical blockers.\n\n- plan/PROD-GAP.md was updated. Ask the user to resolve human-required blockers listed there. Agent may continue with safe P0/P1 technical blockers.\n",
            }
        )
        self.assertEqual([], propose_closeout_entries(ws, "some memory"))

    def test_adjacent_bullets_stay_grouped(self):
        ws = make_workspace(
            {
                "DECISIONS.md": "# D\n\n- **Scope:** company-level shared platform with enough detail to pass the length bar here.\n- **Decision:** unify the console shell now, with enough supporting detail to pass the length bar here.\n",
                "HANDOFF.md": "# H\n",
            }
        )
        proposals = propose_closeout_entries(ws, "some memory")
        self.assertEqual(1, len(proposals))
        self.assertIn("Scope:", proposals[0])
        self.assertIn("Decision:", proposals[0])


class PendingSafety(unittest.TestCase):
    def test_approve_rejects_poisoned_replace(self):
        ws = make_workspace({"memories/MEMORY.md": HAND_MD})
        poison = "# Memory\n\n# Memory\n\nshard\n§\nmore shards\n§\n"
        wid = stage_memory_write(
            ws, target="memory", action="replace", content=poison, reason="t"
        )
        self.assertIsNotNone(wid)
        results = approve_pending(ws, write_id=wid)
        self.assertTrue(any("rejected poisoned" in r for r in results))
        self.assertIn("## Recent", memory_file(ws).read_text(encoding="utf-8"))
        self.assertEqual([], list_pending(ws))

    def test_approve_append_is_markdown_safe_and_idempotent(self):
        ws = make_workspace({"memories/MEMORY.md": HAND_MD})
        wid = stage_memory_write(
            ws, target="memory", action="append", content="A new finding with enough detail to matter.", reason="t"
        )
        approve_pending(ws, write_id=wid)
        out = memory_file(ws).read_text(encoding="utf-8")
        self.assertIn("A new finding", out)
        self.assertNotIn("§", out)
        # Approving the same content twice is a no-op, not a duplicate.
        wid2 = stage_memory_write(
            ws, target="memory", action="append", content="A new finding with enough detail to matter.", reason="t"
        )
        results = approve_pending(ws, write_id=wid2)
        self.assertTrue(any("skipped" in r for r in results))
        self.assertEqual(1, memory_file(ws).read_text(encoding="utf-8").count("A new finding"))

    def test_sectioned_files_keep_their_separator(self):
        ws = make_workspace({"memories/MEMORY.md": "# Memory\n\nfirst\n§\nsecond\n"})
        self.assertTrue(uses_section_sign(memory_file(ws).read_text(encoding="utf-8")))
        wid = stage_memory_write(ws, target="memory", action="append", content="third entry here", reason="t")
        approve_pending(ws, write_id=wid)
        out = memory_file(ws).read_text(encoding="utf-8")
        self.assertIn("third entry here", out)
        self.assertEqual(1, out.count("# Memory"))


class SyncSafety(unittest.TestCase):
    def test_sync_never_writes_memory(self):
        self.assertEqual(ensure_memory_timestamp("anything")[1], [])
        ws = make_workspace(
            {
                "memories/MEMORY.md": HAND_MD,
                "HANDOFF.md": "# H\n",
                "COMPACT.md": "# C\n",
                "TASKS.yml": "tasks: []\n",
                "GATES.yml": "gates: []\n",
            }
        )
        before = memory_file(ws).read_text(encoding="utf-8")
        detect_drift(ws)
        self.assertEqual(before, memory_file(ws).read_text(encoding="utf-8"))


class SessionEndSafety(unittest.TestCase):
    def test_session_end_preserves_markdown_diary(self):
        ws = make_workspace(
            {
                "memories/MEMORY.md": HAND_MD,
                "DECISIONS.md": "# D\n\n- Chose Postgres over DynamoDB for the billing ledger, needs transactions\n",
                "HANDOFF.md": "# H\n\n- Intake agent retry budget capped at three attempts per claim\n",
            }
        )
        for _ in range(3):
            session_end(ws, command="/plan-loop", summary="t")
        out = memory_file(ws).read_text(encoding="utf-8")
        self.assertIn("## Recent", out)
        self.assertEqual(1, out.count("# Memory"))
        self.assertNotIn("§", out)
        self.assertIn("Postgres over DynamoDB", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
