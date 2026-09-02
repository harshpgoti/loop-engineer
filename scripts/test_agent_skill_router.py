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


class TestCapabilitySelection(unittest.TestCase):
    def test_baseline_agentic_engineering_is_selected_for_agent_work(self) -> None:
        selected = router.select_capabilities("build an ai agent")
        self.assertIn("agentic-engineering", selected)

    def test_multi_agent_eval_chain_is_ordered_and_deduplicated(self) -> None:
        selected = router.select_capabilities("multi-agent workflow with golden case evals and dual review")
        self.assertEqual(len(selected), len(set(selected)))
        self.assertLess(selected.index("team-agent-orchestration"), selected.index("eval-harness"))
        self.assertIn("santa-method", selected)

    def test_high_risk_capabilities_are_not_selected_by_generic_agent_signal(self) -> None:
        selected = router.select_capabilities("build an ai agent")
        self.assertNotIn("agent-payment-x402", selected)
        self.assertNotIn("council-multi-model", selected)

    def test_generic_repository_words_do_not_overload_the_chain(self) -> None:
        selected = router.select_capabilities(
            "build an ai agent; the repository has tools, memory files, a developer, and a loop command"
        )
        self.assertNotIn("agent-harness-construction", selected)
        self.assertNotIn("unified-memory", selected)
        self.assertNotIn("dev-team", selected)
        self.assertNotIn("continuous-agent-loop", selected)

    def test_legacy_names_have_canonical_targets(self) -> None:
        self.assertEqual(router.COMPATIBILITY_ALIASES["autonomous-loops"], "continuous-agent-loop")
        self.assertEqual(router.COMPATIBILITY_ALIASES["continuous-learning"], "continuous-learning-v2")

    def test_catalog_exposes_all_requested_capability_names(self) -> None:
        names = {name for name, _signals in router.CAPABILITY_RULES}
        names.update(router.COMPATIBILITY_ALIASES)
        self.assertEqual(30, len(names))

    def test_every_capability_has_a_complete_skill_entrypoint(self) -> None:
        root = Path(__file__).resolve().parents[1]
        names = {name for name, _signals in router.CAPABILITY_RULES}
        names.update(router.COMPATIBILITY_ALIASES)
        for name in names:
            skill = root / "skills" / name / "SKILL.md"
            self.assertTrue(skill.is_file(), f"missing capability entrypoint: {name}")
            text = skill.read_text(encoding="utf-8")
            self.assertIn("Inherits `docs/SKILL_CONTRACT.md`", text)
            self.assertGreater(len(text.splitlines()), 40, f"capability is only a stub: {name}")
            retired_brand = "".join(chr(codepoint) for codepoint in (69, 67, 67))
            self.assertNotIn(retired_brand, text)


class TestFormatAutoAgentSkillsMd(unittest.TestCase):
    def test_includes_always_read_paths(self) -> None:
        from pathlib import Path

        md = router.format_auto_agent_skills_md(
            Path("."), [("agent-builder", "agent-development signals matched")], {}, ""
        )
        for rel in router.ALWAYS_READ:
            self.assertIn(rel, md)
        self.assertIn("loop agent scaffold", md)
        self.assertIn("Capability chain", md)

    def test_explicit_context_capabilities_are_rendered(self) -> None:
        md = router.format_auto_agent_skills_md(
            Path("."),
            [("agent-builder", "agent-development signals matched")],
            {},
            "",
            ["agent-payment-x402"],
        )
        self.assertIn("agent-payment-x402", md)
        self.assertIn("skills/agent-payment-x402/SKILL.md", md)
        self.assertIn("explicit consent required", md)




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
        text = self.mod.render_command("develop-product", "develop-product")
        self.assertIn("commands/develop-product.md", text)

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

    def test_uninstall_removes_the_commands_we_wrote_and_nothing_else(self) -> None:
        """Uninstall used to skip these dirs, leaving `/plan-loop` completing in
        opencode and Pi with the routers already gone."""
        self.mod.install_commands(self.dest, self.names, dry_run=False)
        mine = self.dest / "my-own.md"
        mine.write_text("# mine", encoding="utf-8")
        removed = self.mod.uninstall_commands(self.dest, dry_run=False)
        self.assertEqual(removed, len(self.names) + len(self.mod.ALIASES))
        self.assertTrue(mine.is_file())
        self.assertFalse((self.dest / "plan-loop.md").exists())


class PiHost(unittest.TestCase):
    """Pi (pi.dev) reads `~/.agents/skills`, which install skips at user scope
    because every host was assumed to have its own global dir. Pi had no row, so
    a Pi user got zero routers - and its skills answer to `/skill:<name>`, not
    `/<name>`, so even installed routers do not match what the user types."""

    def setUp(self) -> None:
        import install_skills

        self.mod = install_skills

    def test_pi_is_a_known_host_with_its_own_global_skills_dir(self) -> None:
        self.assertIn("pi", self.mod.HOSTS)
        self.assertEqual("~/.pi/agent/skills", self.mod.HOSTS["pi"]["user"])

    def test_pi_project_scope_collapses_onto_the_universal_dir(self) -> None:
        """Pi reads `.agents/skills` from cwd and ancestors; a second copy in
        `.pi/skills` would list every command twice."""
        self.assertEqual(".agents/skills", self.mod.HOSTS["pi"]["project"])

    def test_pi_gets_prompt_templates_for_the_plain_slash_namespace(self) -> None:
        self.assertIn("pi", self.mod.SLASH_COMMAND_HOSTS)
        self.assertEqual("~/.pi/agent/prompts", self.mod.SLASH_COMMAND_HOSTS["pi"]["user"])
        self.assertEqual(".pi/prompts", self.mod.SLASH_COMMAND_HOSTS["pi"]["project"])

    def test_pi_survives_the_universal_dedupe_at_user_scope(self) -> None:
        kept = self.mod.install_hosts(list(self.mod.HOSTS), "user")
        self.assertIn("pi", kept)
        self.assertNotIn("universal", kept)


class RouterNaming(unittest.TestCase):
    def test_a_skill_name_matches_the_folder_it_lives_in(self) -> None:
        """opencode dedupes skills by name across its scan roots.

        It also auto-loads ~/.claude/skills and ~/.agents/skills, so a name that
        disagrees with the folder stops the copies collapsing: 36 skills became 72.
        """
        import install_skills

        text = install_skills.render_router("plan-loop")
        self.assertIn(f"name: {install_skills.DIR_PREFIX}plan-loop", text)


class RouterTarget(unittest.TestCase):
    """Which app root the routers name.

    Installing from a working checkout repointed every router at that checkout, so
    `/loop-engine` in an unrelated product started reading `<checkout>/AGENTS.md`.
    Nothing in the install output said so.
    """

    def setUp(self) -> None:
        import install_skills

        self.mod = install_skills
        self.addCleanup(self.mod.set_app_root, install_skills.ROOT)

    def test_the_installed_runtime_wins_over_a_checkout(self) -> None:
        chosen = self.mod.router_app_root()
        self.assertTrue(
            chosen == self.mod.ROOT or (chosen / "AGENTS.md").is_file(),
            "router target must be a real app root",
        )

    def test_from_here_aims_at_the_checkout(self) -> None:
        self.assertEqual(self.mod.ROOT, self.mod.router_app_root(from_here=True))

    def test_routers_name_whichever_root_was_chosen(self) -> None:
        self.mod.set_app_root(Path("/somewhere/app"))
        self.assertIn("/somewhere/app/AGENTS.md", self.mod.render_router("status"))
        self.assertIn("/somewhere/app/AGENTS.md", self.mod.render_command("status"))

    def test_the_permission_glob_covers_the_default_home(self) -> None:
        self.assertIn("~/.loop-engineer/**", self.mod.app_globs())


class PermissionGrant(unittest.TestCase):
    """A prompt whose answer is always yes teaches people to click through prompts."""

    def setUp(self) -> None:
        import install_skills

        self.mod = install_skills
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)

    def config(self):
        import json

        return json.loads((self.dir / "opencode.json").read_text(encoding="utf-8"))

    def test_a_missing_config_is_created_with_the_grant(self) -> None:
        _path, added, _note = self.mod.ensure_permissions(self.dir, dry_run=False)
        self.assertIn("~/.loop-engineer/**", added)
        rules = self.config()["permission"]["external_directory"]
        self.assertEqual("allow", rules["~/.loop-engineer/**"])

    def test_the_broad_ask_comes_before_the_allow(self) -> None:
        """opencode applies the LAST matching rule, so ordering is the whole behaviour."""
        self.mod.ensure_permissions(self.dir, dry_run=False)
        keys = list(self.config()["permission"]["external_directory"])
        self.assertEqual("*", keys[0])
        self.assertIn("~/.loop-engineer/**", keys[1:])

    def test_running_twice_changes_nothing(self) -> None:
        self.mod.ensure_permissions(self.dir, dry_run=False)
        _p, added, note = self.mod.ensure_permissions(self.dir, dry_run=False)
        self.assertEqual([], added)
        self.assertEqual("already granted", note)

    def test_an_existing_rule_is_never_overwritten(self) -> None:
        import json

        (self.dir / "opencode.json").write_text(
            json.dumps({"permission": {"external_directory": {"~/.loop-engineer/**": "deny"}}}),
            encoding="utf-8",
        )
        self.mod.ensure_permissions(self.dir, dry_run=False)
        self.assertEqual("deny", self.config()["permission"]["external_directory"]["~/.loop-engineer/**"])

    def test_a_config_we_cannot_parse_is_left_alone(self) -> None:
        """opencode refuses to start on invalid config - never gamble with theirs."""
        jsonc = self.dir / "opencode.jsonc"
        jsonc.write_text(
            chr(123) + " // a comment" + chr(10) + '  "model": "x"' + chr(10) + chr(125),
            encoding="utf-8",
        )
        before = jsonc.read_text(encoding="utf-8")
        _p, added, note = self.mod.ensure_permissions(self.dir, dry_run=False)
        self.assertEqual([], added)
        self.assertIn("not plain JSON", note)
        self.assertEqual(before, jsonc.read_text(encoding="utf-8"))

    def test_other_settings_survive(self) -> None:
        import json

        (self.dir / "opencode.json").write_text(json.dumps({"model": "anthropic/x"}), encoding="utf-8")
        self.mod.ensure_permissions(self.dir, dry_run=False)
        self.assertEqual("anthropic/x", self.config()["model"])

    def test_dry_run_writes_nothing(self) -> None:
        self.mod.ensure_permissions(self.dir, dry_run=True)
        self.assertFalse((self.dir / "opencode.json").exists())


if __name__ == "__main__":
    unittest.main()
