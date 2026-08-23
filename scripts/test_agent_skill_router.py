"""Tests for agent_skill_router.py signal detection and shape classification.

Run: python scripts/test_agent_skill_router.py
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import agent_skill_router as router


class TestHasAgentSignal(unittest.TestCase):
    def test_no_signal_on_generic_web_app(self) -> None:
        text = "a todo list web app with react and postgres"
        self.assertFalse(router.has_agent_signal(text))

    def test_signal_on_ai_agent(self) -> None:
        self.assertTrue(router.has_agent_signal("build an ai agent that triages support tickets"))

    def test_signal_on_workflow_automation(self) -> None:
        self.assertTrue(router.has_agent_signal("automate the workflow for invoice approval"))

    def test_signal_on_chatbot(self) -> None:
        self.assertTrue(router.has_agent_signal("a chatbot for customer support"))


class TestClassifyShape(unittest.TestCase):
    def test_multi_agent_detected(self) -> None:
        shape = router.classify_shape("we need a multi-agent system with an orchestrator agent")
        self.assertTrue(shape["multi_agent"])
        self.assertFalse(shape["rag"])

    def test_rag_detected(self) -> None:
        shape = router.classify_shape("retrieval augmented generation over our vector store")
        self.assertTrue(shape["rag"])

    def test_scheduled_detected(self) -> None:
        shape = router.classify_shape("a cron agent that runs nightly")
        self.assertTrue(shape["scheduled"])

    def test_no_shape_signals(self) -> None:
        shape = router.classify_shape("an ai agent for customer support")
        self.assertFalse(any(shape.values()))


class TestPickSkills(unittest.TestCase):
    def test_empty_when_no_signal(self) -> None:
        self.assertEqual(router.pick_skills("a todo list app"), [])

    def test_returns_agent_builder_with_shape_in_reason(self) -> None:
        picks = router.pick_skills("build a multi-agent workflow automation system")
        self.assertEqual(len(picks), 1)
        name, reason = picks[0]
        self.assertEqual(name, "agent-builder")
        self.assertIn("multi_agent", reason)

    def test_returns_agent_builder_without_shape(self) -> None:
        picks = router.pick_skills("build an ai agent")
        self.assertEqual(picks, [("agent-builder", "agent-development signals matched")])


class TestFormatAutoAgentSkillsMd(unittest.TestCase):
    def test_includes_always_read_paths(self) -> None:
        from pathlib import Path

        md = router.format_auto_agent_skills_md(
            Path("."), [("agent-builder", "agent-development signals matched")], {}, ""
        )
        for rel in router.ALWAYS_READ:
            self.assertIn(rel, md)
        self.assertIn("loop agent scaffold", md)




class SlashCommandInstall(unittest.TestCase):
    """opencode keeps skills and slash commands in separate namespaces.

    Installing only skills left `opencode debug skill` listing all 36 routers while
    `/plan-loop` matched nothing - the user was typing into the namespace we had
    never populated.
    """

    def setUp(self) -> None:
        import install_skills

        self.mod = install_skills
        self.dest = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dest, True)
        self.names = install_skills.command_names()

    def test_opencode_declares_a_separate_command_directory(self) -> None:
        self.assertIn("opencode", self.mod.SLASH_COMMAND_HOSTS)
        # opencode's own documented layout is singular `command/`.
        self.assertTrue(self.mod.SLASH_COMMAND_HOSTS["opencode"]["user"].endswith("/command"))

    def test_every_command_gets_a_file_named_for_the_slash_command(self) -> None:
        written, _ = self.mod.install_commands(self.dest, self.names, dry_run=False)
        self.assertEqual(written, len(self.names) + len(self.mod.ALIASES))
        self.assertTrue((self.dest / "plan-loop.md").is_file())
        self.assertTrue((self.dest / "diagnose-loop.md").is_file())

    def test_a_command_file_carries_a_description_and_no_name_key(self) -> None:
        """The filename is the command; a `name:` key would be a second source of truth."""
        text = self.mod.render_command("plan-loop")
        self.assertTrue(text.startswith("---"))
        self.assertIn("description:", text)
        self.assertNotIn("@name:", text.replace(chr(10), "@"))

    def test_the_body_routes_to_the_installed_app(self) -> None:
        text = self.mod.render_command("plan-loop")
        self.assertIn("commands/plan-loop.md", text)
        self.assertIn("AGENTS.md", text)

    def test_an_alias_runs_its_target_command(self) -> None:
        text = self.mod.render_command("develop-product", "product-develop")
        self.assertIn("commands/product-develop.md", text)

    def test_a_hand_written_command_is_never_clobbered(self) -> None:
        mine = self.dest / "plan-loop.md"
        mine.write_text("# my own command", encoding="utf-8")
        self.mod.install_commands(self.dest, self.names, dry_run=False)
        self.assertEqual("# my own command", mine.read_text(encoding="utf-8"))

    def test_a_command_we_own_that_no_longer_exists_is_pruned(self) -> None:
        stale = self.dest / "retired-loop.md"
        stale.write_text(f"<!-- {self.mod.MARKER} name=retired-loop -->", encoding="utf-8")
        _, pruned = self.mod.install_commands(self.dest, self.names, dry_run=False)
        self.assertEqual(1, pruned)
        self.assertFalse(stale.exists())

    def test_dry_run_writes_nothing(self) -> None:
        self.mod.install_commands(self.dest, self.names, dry_run=True)
        self.assertEqual([], list(self.dest.glob("*.md")))


class RouterNaming(unittest.TestCase):
    def test_a_skill_name_matches_the_folder_it_lives_in(self) -> None:
        """opencode dedupes skills by name across its scan roots.

        It also auto-loads ~/.claude/skills and ~/.agents/skills, so a name that
        disagrees with the folder stops the copies collapsing: 36 skills became 72.
        """
        import install_skills

        text = install_skills.render_router("plan-loop")
        self.assertIn(f"name: {install_skills.DIR_PREFIX}plan-loop", text)


if __name__ == "__main__":
    unittest.main()
