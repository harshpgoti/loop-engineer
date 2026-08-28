from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from runtime_update import update_runtime


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


class RuntimeUpdate(unittest.TestCase):
    def test_dirty_runtime_is_backed_up_and_updated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            remote = base / "remote.git"
            seed = base / "seed"
            app = base / "app"
            subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
            subprocess.run(["git", "clone", str(remote), str(seed)], check=True, capture_output=True)
            git(seed, "config", "user.email", "loop@example.test")
            git(seed, "config", "user.name", "Loop Test")
            (seed / "version.txt").write_text("one", encoding="utf-8")
            git(seed, "add", "version.txt")
            git(seed, "commit", "-m", "one")
            git(seed, "branch", "-M", "main")
            git(seed, "push", "-u", "origin", "main")
            subprocess.run(["git", "clone", "--branch", "main", str(remote), str(app)], check=True, capture_output=True)
            (app / "version.txt").write_text("local edit", encoding="utf-8")
            (app / "untracked.txt").write_text("keep me", encoding="utf-8")
            (seed / "version.txt").write_text("two", encoding="utf-8")
            git(seed, "commit", "-am", "two")
            git(seed, "push")

            code, notes = update_runtime(app)

            self.assertEqual(0, code, notes)
            self.assertEqual("two", (app / "version.txt").read_text(encoding="utf-8"))
            self.assertFalse((app / "untracked.txt").exists())
            self.assertIn("loop-engineer-auto-backup", git(app, "stash", "list"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
