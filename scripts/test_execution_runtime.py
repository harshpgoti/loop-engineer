from __future__ import annotations

import subprocess
import json
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from execution_runtime import ExecutionRuntime, ExecutionError
from execution_supervisor import SupervisorController


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=True)
    return result.stdout.strip()


class ExecutionRuntimeContract(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.repo = base / "repo"
        self.data = base / "workspace" / ".loop-engineer"
        self.repo.mkdir(parents=True)
        self.data.mkdir(parents=True)
        git(self.repo, "init")
        git(self.repo, "config", "user.email", "loop@example.test")
        git(self.repo, "config", "user.name", "Loop Test")
        (self.repo / "README.md").write_text("base\n", encoding="utf-8")
        git(self.repo, "add", "README.md")
        git(self.repo, "commit", "-m", "base")
        self.runtime = ExecutionRuntime(self.data)

    def test_prepare_compiles_brief_and_refuses_duplicate_active_task(self) -> None:
        run = self.runtime.prepare("TASK-1", "delivery", self.repo, "Build it", ["works"])
        self.assertEqual("TASK-1", run["task_id"])
        self.assertNotEqual(self.repo.resolve(), Path(run["worktree"]).resolve())
        self.assertIn("works", (Path(run["run_dir"]) / "brief.md").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ExecutionError, "active run"):
            self.runtime.prepare("TASK-1", "delivery", self.repo, "Again", ["no"])

    def test_worktree_allocation_refuses_a_dirty_primary_checkout(self) -> None:
        (self.repo / "dirty.txt").write_text("dirty", encoding="utf-8")
        with self.assertRaisesRegex(ExecutionError, "dirty"):
            self.runtime.prepare("TASK-DIRTY-BASE", "research", self.repo, "No", ["clean"])

    def test_only_one_delivery_run_can_be_active_in_a_workspace(self) -> None:
        self.runtime.prepare("TASK-A", "delivery", self.repo, "A", ["a"])
        with self.assertRaisesRegex(ExecutionError, "delivery run"):
            self.runtime.prepare("TASK-B", "delivery", self.repo, "B", ["b"])

    def test_delivery_lease_is_atomic_across_simultaneous_spawns(self) -> None:
        def attempt(task_id: str) -> str:
            try:
                self.runtime.prepare(task_id, "delivery", self.repo, task_id, ["done"])
                return "created"
            except ExecutionError:
                return "refused"
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(attempt, ("TASK-RACE-A", "TASK-RACE-B")))
        self.assertEqual(["created", "refused"], sorted(outcomes))

    def test_events_are_generation_bound_and_fold_to_latest_state(self) -> None:
        run = self.runtime.prepare("TASK-2", "research", self.repo, "Research", ["report"])
        self.runtime.append_event(run["run_id"], "working", "started", run["generation"])
        with self.assertRaisesRegex(ExecutionError, "generation"):
            self.runtime.append_event(run["run_id"], "failed", "stale", run["generation"] + 1)
        self.assertEqual("working", self.runtime.status(run["run_id"])["state"])

    def test_cleanup_releases_a_delivery_run_with_no_unlanded_commits(self) -> None:
        run = self.runtime.prepare("TASK-CLEAN", "delivery", self.repo, "Inspect", ["no changes"])
        branch = run["branch"]
        self.runtime.cleanup(run["run_id"])
        self.assertEqual("torn_down", self.runtime.status(run["run_id"])["state"])
        self.assertNotIn(branch, git(self.repo, "branch", "--list", branch))
        self.assertFalse(Path(run["lease"]).exists())

    def test_cleanup_refuses_dirty_and_unlanded_delivery_work(self) -> None:
        run = self.runtime.prepare("TASK-4", "delivery", self.repo, "Change", ["done"])
        worktree = Path(run["worktree"])
        (worktree / "dirty.txt").write_text("dirty", encoding="utf-8")
        with self.assertRaisesRegex(ExecutionError, "dirty"):
            self.runtime.cleanup(run["run_id"])
        (worktree / "dirty.txt").unlink()
        (worktree / "README.md").write_text("commit\n", encoding="utf-8")
        git(worktree, "commit", "-am", "unlanded")
        with self.assertRaisesRegex(ExecutionError, "not landed"):
            self.runtime.cleanup(run["run_id"])

    def test_spawn_appends_brief_pointer_persists_pid_and_can_stop(self) -> None:
        run = self.runtime.spawn("TASK-SPAWN", "delivery", self.repo, "Run", ["stop"], [sys.executable, "-c", "import time; time.sleep(60)"], executor="builder")
        self.assertGreater(run["pid"], 0)
        self.assertEqual("launched", self.runtime.status(run["run_id"])["state"])
        self.assertIn("Read the execution brief at", run["launch_command"][-1])
        self.runtime.stop(run["run_id"])
        self.assertEqual("stopped", self.runtime.status(run["run_id"])["state"])

    def test_events_can_be_read_after_runtime_restart(self) -> None:
        run = self.runtime.prepare("TASK-RESTART", "research", self.repo, "Research", ["report"])
        self.runtime.append_event(run["run_id"], "working", "durable", run["generation"])
        restarted = ExecutionRuntime(self.data)
        self.assertEqual("working", restarted.status(run["run_id"])["state"])
        self.assertEqual(["created", "working"], [row["event"] for row in restarted.events(run["run_id"])])

    def test_reconcile_preserves_interrupted_preparation_identity(self) -> None:
        run = self.runtime.prepare("TASK-RECOVER", "research", self.repo, "Research", ["report"])
        registry = self.runtime.list_runs()
        registry["runs"][run["run_id"]]["state"] = "preparing"
        self.runtime._save(registry)
        restarted = ExecutionRuntime(self.data)
        findings = restarted.reconcile()
        self.assertTrue(findings)
        self.assertEqual("blocked", restarted.status(run["run_id"])["state"])

    def test_worker_cli_compiles_context_and_runs_full_phase_one_lifecycle(self) -> None:
        (self.data / "TASKS.yml").write_text(
            "tasks:\n  - id: TASK-CLI\n    title: CLI worker\n    gate: GATE-CLI\n    acceptance:\n      - pointer launch works\n",
            encoding="utf-8",
        )
        (self.data / "GATES.yml").write_text("gates:\n  GATE-CLI:\n    status: pending\n", encoding="utf-8")
        cli = Path(__file__).with_name("loop_cli.py")
        spawn = subprocess.run(
            [sys.executable, str(cli), "worker", "spawn", "TASK-CLI", "--repository", str(self.repo), "--workspace", str(self.data), "--command-json", json.dumps([sys.executable, "-c", "import time; time.sleep(60)"])],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(0, spawn.returncode, spawn.stdout + spawn.stderr)
        run = json.loads(spawn.stdout)
        self.addCleanup(lambda: ExecutionRuntime(self.data).stop(run["run_id"]) if ExecutionRuntime._pid_alive(run["pid"]) else None)
        brief = (Path(run["run_dir"]) / "brief.md").read_text(encoding="utf-8")
        self.assertIn("Canonical task record", brief)
        self.assertIn("GATE-CLI", brief)
        status = subprocess.run([sys.executable, str(cli), "worker", "status", run["run_id"], "--workspace", str(self.data)], text=True, capture_output=True, check=True)
        self.assertEqual(run["run_id"], json.loads(status.stdout)["run_id"])
        subprocess.run([sys.executable, str(cli), "worker", "stop", run["run_id"], "--workspace", str(self.data)], text=True, capture_output=True, check=True)
        events = subprocess.run([sys.executable, str(cli), "worker", "events", run["run_id"], "--workspace", str(self.data)], text=True, capture_output=True, check=True)
        self.assertEqual("stopped", json.loads(events.stdout)[-1]["event"])
        teardown = subprocess.run([sys.executable, str(cli), "worker", "teardown", run["run_id"], "--workspace", str(self.data)], text=True, capture_output=True, check=True)
        self.assertEqual("torn_down", json.loads(teardown.stdout)["state"])

    def test_research_report_reconciles_evidence_exactly_once(self) -> None:
        run = self.runtime.prepare("TASK-RESEARCH", "research", self.repo, "Research", ["cite"])
        self.runtime.record_research(run["run_id"], "A grounded finding.", ["https://example.test/source"], ["Choose retention policy"])
        evidence = self.data / "EVIDENCE_LOG.md"
        self.runtime.reconcile_research(run["run_id"], evidence)
        self.runtime.reconcile_research(run["run_id"], evidence)
        text = evidence.read_text(encoding="utf-8")
        self.assertEqual(1, text.count(f"loop-worker:{run['run_id']}"))
        self.assertIn("Date checked", text)

    def test_validation_is_separate_read_only_and_bound_to_base_and_head(self) -> None:
        delivery = self.runtime.prepare("TASK-VALIDATE", "delivery", self.repo, "Change", ["review"], delivery_mode="local-only", executor="builder")
        worktree = Path(delivery["worktree"])
        (worktree / "README.md").write_text("candidate\n", encoding="utf-8")
        git(worktree, "commit", "-am", "candidate")
        with self.assertRaisesRegex(ExecutionError, "cannot validate itself"):
            self.runtime.start_validation(delivery["run_id"], "builder")
        validation = self.runtime.start_validation(delivery["run_id"], "reviewer")
        self.assertTrue(validation["readonly"])
        review = self.runtime.submit_validation(validation["run_id"], "pass", "Spec passes", "Standards pass")
        self.assertEqual(git(worktree, "rev-parse", "HEAD"), review["head_commit"])
        (worktree / "README.md").write_text("changed after review\n", encoding="utf-8")
        git(worktree, "commit", "-am", "invalidate")
        with self.assertRaisesRegex(ExecutionError, "stale"):
            self.runtime.verify_merge_ready(delivery["run_id"])

    def test_inbox_actions_and_event_deduplication_survive_restart(self) -> None:
        run = self.runtime.prepare("TASK-EVENTS", "research", self.repo, "Observe", ["durable"])
        message = self.runtime.send(run["run_id"], "Change direction")
        restarted = ExecutionRuntime(self.data)
        self.assertEqual(1, restarted.fold_state(run["run_id"])["pending_messages"])
        restarted.acknowledge_message(run["run_id"], message.name, generation=1)
        first = restarted.append_event(run["run_id"], "blocked", "needs authority", 1, event_id="stable-action")
        second = restarted.append_event(run["run_id"], "blocked", "duplicate", 1, event_id="stable-action")
        self.assertEqual(first, second)
        self.assertEqual(1, len(restarted.actions()))
        restarted.acknowledge_action("stable-action")
        self.assertEqual([], restarted.actions())

    def test_relaunch_increments_generation_and_rejects_old_messages(self) -> None:
        run = self.runtime.spawn("TASK-RELAUNCH", "research", self.repo, "Restart", ["generation"], [sys.executable, "-c", "import time; time.sleep(60)"])
        relaunched = self.runtime.relaunch(run["run_id"])
        self.addCleanup(lambda: self.runtime.stop(run["run_id"]) if self.runtime._pid_alive(self.runtime.status(run["run_id"])["pid"]) else None)
        self.assertEqual(2, relaunched["generation"])
        with self.assertRaisesRegex(ExecutionError, "generation"):
            self.runtime.send(run["run_id"], "stale", generation=1)
        self.runtime.stop(run["run_id"])

    def test_relaunch_refuses_a_mutated_immutable_brief(self) -> None:
        run = self.runtime.spawn("TASK-BRIEF-HASH", "research", self.repo, "Restart", ["immutable"], [sys.executable, "-c", "import time; time.sleep(60)"])
        self.runtime.stop(run["run_id"])
        brief = Path(run["run_dir"]) / "brief.md"
        brief.write_text(brief.read_text(encoding="utf-8") + "mutated\n", encoding="utf-8")
        with self.assertRaisesRegex(ExecutionError, "brief changed"):
            self.runtime.relaunch(run["run_id"])

    def test_local_shipping_requires_review_current_head_and_explicit_approval(self) -> None:
        delivery = self.runtime.prepare("TASK-SHIP", "delivery", self.repo, "Ship", ["land"], delivery_mode="local-only", executor="builder")
        worktree = Path(delivery["worktree"])
        (worktree / "README.md").write_text("shipped\n", encoding="utf-8")
        git(worktree, "commit", "-am", "ship")
        validation = self.runtime.start_validation(delivery["run_id"], "reviewer")
        self.runtime.submit_validation(validation["run_id"], "pass", "pass", "pass")
        with self.assertRaisesRegex(ExecutionError, "approval token"):
            self.runtime.merge_local(delivery["run_id"], "master", approval="no")
        head = self.runtime.merge_local(delivery["run_id"], "master", approval=f"approve:{delivery['run_id']}")
        self.assertEqual(head, git(self.repo, "rev-parse", "HEAD"))
        tasks = self.data / "TASKS.yml"
        gates = self.data / "GATES.yml"
        tasks.write_text("tasks:\n  - id: TASK-SHIP\n    status: in_progress\n    gate: GATE-SHIP\n", encoding="utf-8")
        gates.write_text("gates:\n  GATE-SHIP:\n    status: pending\n", encoding="utf-8")
        journal = self.runtime.reconcile_product_truth(delivery["run_id"], tasks, gates)
        self.assertIn("status: completed", tasks.read_text(encoding="utf-8"))
        self.assertIn("status: passed", gates.read_text(encoding="utf-8"))
        self.assertEqual("applied", json.loads(journal.read_text(encoding="utf-8"))["state"])

    def test_remote_delivery_modes_require_durable_exact_head_evidence(self) -> None:
        delivery = self.runtime.prepare("TASK-PR", "delivery", self.repo, "PR", ["verified"], delivery_mode="direct-pr", executor="builder")
        worktree = Path(delivery["worktree"])
        (worktree / "README.md").write_text("pr\n", encoding="utf-8"); git(worktree, "commit", "-am", "pr")
        validation = self.runtime.start_validation(delivery["run_id"], "reviewer"); self.runtime.submit_validation(validation["run_id"], "pass", "pass", "pass")
        head = git(worktree, "rev-parse", "HEAD")
        with self.assertRaisesRegex(ExecutionError, "remote PR head"):
            self.runtime.verify_merge_ready(delivery["run_id"])
        bad_gh = Path(self.tmp.name) / "bad_gh.py"
        bad_gh.write_text("import json\nprint(json.dumps({'headRefOid':'0000000000000000000000000000000000000000','state':'OPEN','url':'x','statusCheckRollup':[]}))\n", encoding="utf-8")
        with self.assertRaisesRegex(ExecutionError, "does not match"):
            self.runtime.refresh_github_evidence(delivery["run_id"], "1", gh=[sys.executable, str(bad_gh)])
        fake_gh = Path(self.tmp.name) / "fake_gh.py"
        fake_gh.write_text(f"import json\nprint(json.dumps({{'headRefOid':'{head}','state':'OPEN','url':'https://example.test/pr/1','statusCheckRollup':[{{'conclusion':'SUCCESS'}}]}}))\n", encoding="utf-8")
        evidence = self.runtime.refresh_github_evidence(delivery["run_id"], "1", gh=[sys.executable, str(fake_gh)])
        self.assertEqual("passed", evidence["pipeline_state"])
        self.assertEqual(head, self.runtime.verify_merge_ready(delivery["run_id"])["head"])

    def test_quota_dispatch_is_priority_ordered_and_dependency_aware(self) -> None:
        (self.data / "workers").mkdir(parents=True, exist_ok=True)
        (self.data / "workers" / "policy.json").write_text(json.dumps({"schema_version": 1, "max_active": 1, "max_delivery": 1, "max_research": 1, "wedge_after_seconds": 900, "poll_seconds": 1}), encoding="utf-8")
        command = [sys.executable, "-c", "import time; time.sleep(60)"]
        blocked = self.runtime.enqueue_dispatch("TASK-DEPENDENT", self.repo, command, kind="research", priority=1, depends_on=["TASK-MISSING"])
        first = self.runtime.enqueue_dispatch("TASK-PRIORITY", self.repo, command, kind="research", priority=10)
        second = self.runtime.enqueue_dispatch("TASK-LATER", self.repo, command, kind="research", priority=20)
        dispatched = self.runtime.dispatch_once()
        self.assertEqual(["TASK-PRIORITY"], [run["task_id"] for run in dispatched])
        queue_path = self.data / "workers" / "dispatch.json"
        crash_queue = json.loads(queue_path.read_text(encoding="utf-8"))
        priority_row = next(row for row in crash_queue["requests"] if row["request_id"] == first["request_id"])
        priority_row["state"] = "queued"; priority_row.pop("run_id", None)
        queue_path.write_text(json.dumps(crash_queue), encoding="utf-8")
        self.assertTrue(self.runtime.reconcile_dispatch_queue())
        self.assertEqual("dispatched", next(row for row in self.runtime.dispatch_queue() if row["request_id"] == first["request_id"])["state"])
        self.assertEqual("queued", next(row for row in self.runtime.dispatch_queue() if row["request_id"] == blocked["request_id"])["state"])
        self.assertEqual("queued", next(row for row in self.runtime.dispatch_queue() if row["request_id"] == second["request_id"])["state"])
        self.runtime.stop(dispatched[0]["run_id"])
        later = self.runtime.dispatch_once()
        self.assertEqual(["TASK-LATER"], [run["task_id"] for run in later])
        self.runtime.stop(later[0]["run_id"])

    def test_concurrent_enqueue_does_not_lose_requests(self) -> None:
        command = [sys.executable, "-c", "print('queued')"]
        with ThreadPoolExecutor(max_workers=6) as pool:
            requests = list(pool.map(lambda number: self.runtime.enqueue_dispatch(f"TASK-QUEUE-{number}", self.repo, command, kind="research"), range(12)))
        self.assertEqual(12, len({row["request_id"] for row in requests}))
        self.assertEqual(12, len(self.runtime.dispatch_queue()))

    def test_persistent_supervisor_refuses_duplicate_start_and_stops_cleanly(self) -> None:
        controller = SupervisorController(self.data)
        state = controller.start()
        self.addCleanup(lambda: controller.stop() if controller.status().get("state") == "running" else None)
        self.assertEqual("running", state["state"])
        with self.assertRaisesRegex(ExecutionError, "already running"):
            controller.start()
        deadline = time.time() + 5
        heartbeat = self.data / "workers" / "supervisor-heartbeat.json"
        while not heartbeat.exists() and time.time() < deadline:
            time.sleep(0.1)
        self.assertTrue(heartbeat.exists())
        stopped = controller.stop()
        self.assertEqual("stopped", stopped["state"])
        restarted = controller.start()
        self.assertEqual(state["generation"] + 1, restarted["generation"])
        controller.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
