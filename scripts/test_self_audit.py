from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import self_audit


ROOT = Path(__file__).resolve().parents[1]


def _populate_workspace(root: Path) -> None:
    """Create a minimal LE app workspace for the self-audit script to walk.

    The workspace must have a complete enough surface that the self-audit
    finds zero findings. In practice this means: a manifest per role, every
    direct-invocation skill has a matching command file, and the activation
    paths are wired.
    """
    (root / "manifests").mkdir(parents=True, exist_ok=True)
    (root / "skills").mkdir(parents=True, exist_ok=True)
    (root / "commands").mkdir(parents=True, exist_ok=True)
    (root / "AGENTS.md").write_text(
        "# AGENTS\n\n"
        "Refer to commands/ok-cmd.md and skills/ok-skill/SKILL.md.\n",
        encoding="utf-8",
    )
    (root / "manifests" / "skill_policy.json").write_text(json.dumps({
        "version": 1,
        "classes": {"read-only": {"required_terms": ["evidence", "output"]}},
        "assignments": {"ok-skill": "read-only"},
    }), encoding="utf-8")
    (root / "manifests" / "capabilities.json").write_text(json.dumps({
        "version": 1,
        "capabilities": [{"id": "foundation", "summary": "x", "commands": ["ok-cmd"], "skills": ["ok-skill"], "requires": [], "context_cost": 5}],
    }), encoding="utf-8")
    (root / "manifests" / "agents.json").write_text(json.dumps({
        "version": 1,
        "roles": [
            {"id": "r1", "class": "planner", "skills": ["ok-skill"], "may_mutate": False, "independent_from": []},
        ],
    }), encoding="utf-8")
    (root / "manifests" / "install_profiles.json").write_text(json.dumps({
        "version": 1,
        "profiles": [{"id": "minimal", "summary": "x", "capabilities": ["foundation"], "context_budget": 50}],
    }), encoding="utf-8")
    (root / "skills" / "ok-skill" / "SKILL.md").parent.mkdir(parents=True, exist_ok=True)
    (root / "skills" / "ok-skill" / "SKILL.md").write_text("# OK\n", encoding="utf-8")
    (root / "commands" / "ok-cmd.md").write_text("# /ok-cmd\n", encoding="utf-8")


def _populate_workspace_from_real_le(root: Path) -> None:
    """Mirror the real LE app's skills/, commands/, harnesses/ into a temp workspace.

    This lets the test run the audit end-to-end against a real-shaped surface
    without depending on the production DIRECT_INVOCATION_SKILLS being a no-op.
    """
    real_root = Path(__file__).resolve().parents[1]
    for name in ("manifests", "AGENTS.md"):
        src = real_root / name
        dst = root / name
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            for child in src.iterdir():
                if child.is_file():
                    (dst / child.name).write_bytes(child.read_bytes())
        else:
            dst.write_bytes(src.read_bytes())
    (root / "skills").mkdir(parents=True, exist_ok=True)
    (root / "commands").mkdir(parents=True, exist_ok=True)
    (root / "harnesses").mkdir(parents=True, exist_ok=True)


class SelfAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        _populate_workspace(self.tmp)

    def test_clean_mirrored_workspace_reports_zero_findings(self) -> None:
        # The real LE app's full skill/command/manifest surface, copied
        # to a temp workspace, should pass the audit with zero findings.
        real_root = Path(__file__).resolve().parents[1]
        import shutil
        # Mirror the real LE app.
        for sub in ("manifests", "AGENTS.md"):
            src = real_root / sub
            dst = self.tmp / sub
            if src.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
                for child in src.iterdir():
                    (dst / child.name).write_bytes(child.read_bytes())
            else:
                dst.write_bytes(src.read_bytes())
        for sub in ("skills", "commands", "harnesses"):
            src_dir = real_root / sub
            dst_dir = self.tmp / sub
            if dst_dir.exists():
                shutil.rmtree(dst_dir)
            shutil.copytree(src_dir, dst_dir)
        import sys, io
        from contextlib import redirect_stdout
        backup = sys.argv
        try:
            sys.argv = ["self_audit.py", "--root", str(self.tmp), "--json"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                self_audit.main()
            data = json.loads(buf.getvalue())
        finally:
            sys.argv = backup
        self.assertEqual(
            [], data["findings"],
            f"unexpected findings: {data['findings'][:3]}",
        )

    def test_command_skill_consistency_check(self) -> None:
        # Unit test: the _check_command_skill_consistency function flags a
        # direct-invocation skill without a matching command file. The
        # test uses a minimal allowlist so it does not depend on the full
        # production DIRECT_INVOCATION_SKILLS list.
        from self_audit import _check_command_skill_consistency
        # Set up a temp workspace with a skill that has no command.
        (self.tmp / "skills" / "test-skill" / "SKILL.md").parent.mkdir(parents=True, exist_ok=True)
        (self.tmp / "skills" / "test-skill" / "SKILL.md").write_text("# test\n", encoding="utf-8")
        # Monkey-patch the constant for this test only.
        import self_audit
        original = self_audit.DIRECT_INVOCATION_SKILLS
        try:
            self_audit.DIRECT_INVOCATION_SKILLS = frozenset({"test-skill"})
            findings = _check_command_skill_consistency(
                self.tmp, {"test-skill"}, set(),
            )
            self.assertTrue(any("test-skill" in f for f in findings))
        finally:
            self_audit.DIRECT_INVOCATION_SKILLS = original

        # Add the command file; finding should clear.
        (self.tmp / "commands" / "test-skill.md").write_text("# /test-skill\n", encoding="utf-8")
        import self_audit
        original = self_audit.DIRECT_INVOCATION_SKILLS
        try:
            self_audit.DIRECT_INVOCATION_SKILLS = frozenset({"test-skill"})
            findings = _check_command_skill_consistency(
                self.tmp, {"test-skill"}, {"test-skill"},
            )
            self.assertEqual([], findings)
        finally:
            self_audit.DIRECT_INVOCATION_SKILLS = original


if __name__ == "__main__":
    unittest.main()