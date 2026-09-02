"""Tests for scripts/skill_list.py and scripts/roles_list.py."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import skill_list
import roles_list


REAL_ROOT = Path(__file__).resolve().parents[1]


class SkillListTests(unittest.TestCase):
    def test_json_output_includes_all_skills(self) -> None:
        backup = sys.argv
        try:
            sys.argv = ["skill_list.py", "--root", str(REAL_ROOT), "--json"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                skill_list.main()
            data = json.loads(buf.getvalue())
        finally:
            sys.argv = backup
        self.assertGreater(data["count"], 50)
        skill_names = {row["skill"] for row in data["skills"]}
        self.assertIn("code-reviewer", skill_names)
        self.assertIn("council", skill_names)
        # Every row has class and capability
        for row in data["skills"]:
            self.assertIn("class", row)
            self.assertIn("capability", row)

    def test_class_filter(self) -> None:
        backup = sys.argv
        try:
            sys.argv = ["skill_list.py", "--root", str(REAL_ROOT), "--json", "--class", "assurance"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                skill_list.main()
            data = json.loads(buf.getvalue())
        finally:
            sys.argv = backup
        for row in data["skills"]:
            self.assertEqual("assurance", row["class"])

    def test_markdown_output_contains_table(self) -> None:
        backup = sys.argv
        try:
            sys.argv = ["skill_list.py", "--root", str(REAL_ROOT)]
            buf = io.StringIO()
            with redirect_stdout(buf):
                skill_list.main()
            output = buf.getvalue()
        finally:
            sys.argv = backup
        self.assertIn("Total skills:", output)
        self.assertIn("| Skill |", output)


class RolesListTests(unittest.TestCase):
    def test_json_output_includes_all_roles(self) -> None:
        backup = sys.argv
        try:
            sys.argv = ["roles_list.py", "--root", str(REAL_ROOT), "--json"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                roles_list.main()
            data = json.loads(buf.getvalue())
        finally:
            sys.argv = backup
        self.assertGreater(data["count"], 15)
        role_ids = {role["id"] for role in data["roles"]}
        self.assertIn("code-reviewer", role_ids)
        self.assertIn("builder", role_ids)
        # Every role has class and model
        for role in data["roles"]:
            self.assertIn("class", role)
            self.assertIn("model", role)

    def test_class_filter(self) -> None:
        backup = sys.argv
        try:
            sys.argv = ["roles_list.py", "--root", str(REAL_ROOT), "--json", "--class", "planner"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                roles_list.main()
            data = json.loads(buf.getvalue())
        finally:
            sys.argv = backup
        for role in data["roles"]:
            self.assertEqual("planner", role["class"])

    def test_markdown_output_contains_table(self) -> None:
        backup = sys.argv
        try:
            sys.argv = ["roles_list.py", "--root", str(REAL_ROOT)]
            buf = io.StringIO()
            with redirect_stdout(buf):
                roles_list.main()
            output = buf.getvalue()
        finally:
            sys.argv = backup
        self.assertIn("Total roles:", output)
        self.assertIn("| Role |", output)


if __name__ == "__main__":
    unittest.main()