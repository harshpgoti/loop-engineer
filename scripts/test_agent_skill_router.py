"""Tests for agent_skill_router.py signal detection and shape classification.

Run: python scripts/test_agent_skill_router.py
"""

from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
