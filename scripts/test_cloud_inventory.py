"""The record of what a deploy actually created, and what can safely be deleted."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cloud_inventory as ci  # noqa: E402


class Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        self.ws = self.root / "Product" / ".loop-engineer"
        (self.ws / "plan").mkdir(parents=True)

    def add(self, **kw):
        base = dict(
            env="dev",
            provider="aws",
            service="RDS",
            resource="db-1",
            purpose="denial engine database",
            region="ca-central-1",
        )
        base.update(kw)
        return ci.add(self.ws, **base)


class Recording(Sandbox):
    def test_a_resource_round_trips_through_the_table(self) -> None:
        self.add(teardown="aws rds delete-db-instance --db-instance-identifier db-1")
        [item] = ci.parse(self.ws)
        self.assertEqual(item.id, "R-001")
        self.assertEqual(item.env, "dev")
        self.assertEqual(item.resource, "db-1")
        self.assertEqual(item.purpose, "denial engine database")
        self.assertIn("delete-db-instance", item.teardown)
        self.assertTrue(item.live)

    def test_ids_increment(self) -> None:
        self.add(resource="db-1")
        self.add(resource="db-2")
        self.assertEqual([r.id for r in ci.parse(self.ws)], ["R-001", "R-002"])

    def test_recording_the_same_resource_twice_updates_it(self) -> None:
        """A deploy gets re-run; a retry must not create a second row for one resource."""
        self.add(purpose="first")
        self.add(purpose="second guess")
        rows = ci.parse(self.ws)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].purpose, "second guess")

    def test_the_same_name_in_two_environments_is_two_resources(self) -> None:
        self.add(env="dev", resource="api")
        self.add(env="prod", resource="api")
        self.assertEqual(len(ci.parse(self.ws)), 2)

    def test_the_table_is_grouped_by_environment(self) -> None:
        self.add(env="prod", resource="api-prod")
        self.add(env="dev", resource="api-dev")
        text = ci.inventory_path(self.ws).read_text(encoding="utf-8")
        self.assertLess(text.index("## dev"), text.index("## prod"))

    def test_a_deleted_resource_keeps_its_row(self) -> None:
        """That it existed and was removed is history worth keeping."""
        record = self.add()
        ci.mark(self.ws, record.id, ci.STATUS_DELETED)
        [item] = ci.parse(self.ws)
        self.assertEqual(item.status, ci.STATUS_DELETED)
        self.assertFalse(item.live)

    def test_an_empty_workspace_reads_as_empty_not_an_error(self) -> None:
        self.assertEqual(ci.parse(self.ws), [])

    def test_a_malformed_row_is_skipped_rather_than_fatal(self) -> None:
        self.add()
        path = ci.inventory_path(self.ws)
        path.write_text(path.read_text(encoding="utf-8") + "\n| | | broken\n", encoding="utf-8")
        self.assertEqual(len(ci.parse(self.ws)), 1)


class WhatCanIDelete(Sandbox):
    def test_old_dev_resources_are_teardown_candidates(self) -> None:
        old = (date.today() - timedelta(days=30)).isoformat()
        ci.add(
            self.ws, env="dev", provider="aws", service="ECS", resource="spike-cluster",
            purpose="trying fargate", created=old,
        )
        rows = [t for t in ci.teardown_candidates(self.ws) if "still recent" not in t.reason]
        self.assertEqual(len(rows), 1)
        self.assertIn("30 days old", rows[0].reason)

    def test_a_fresh_dev_resource_is_not_called_finished(self) -> None:
        self.add()
        rows = [t for t in ci.teardown_candidates(self.ws) if "still recent" not in t.reason]
        self.assertEqual(rows, [])

    def test_prod_and_staging_are_never_teardown_candidates(self) -> None:
        """Deletion is irreversible; guessing about production is not acceptable."""
        old = (date.today() - timedelta(days=400)).isoformat()
        for env in ("prod", "staging"):
            ci.add(
                self.ws, env=env, provider="aws", service="RDS", resource=f"db-{env}",
                purpose="live data", created=old,
            )
        self.assertEqual(ci.teardown_candidates(self.ws), [])

    def test_an_already_deleted_resource_is_not_offered_again(self) -> None:
        old = (date.today() - timedelta(days=30)).isoformat()
        record = ci.add(
            self.ws, env="dev", provider="aws", service="ECS", resource="gone",
            purpose="x", created=old,
        )
        ci.mark(self.ws, record.id, ci.STATUS_DELETED)
        self.assertEqual(ci.teardown_candidates(self.ws), [])

    def test_a_hand_edited_row_with_no_date_is_flagged_rather_than_assumed_fresh(self) -> None:
        """`add` always stamps a date; a row someone typed by hand may not have one."""
        record = self.add()
        path = ci.inventory_path(self.ws)
        path.write_text(path.read_text(encoding="utf-8").replace(record.created, ""), encoding="utf-8")
        rows = ci.teardown_candidates(self.ws)
        self.assertIn("no creation date", rows[0].reason)


class Attribution(Sandbox):
    def test_a_resource_with_no_purpose_is_reported(self) -> None:
        ci.add(self.ws, env="prod", provider="aws", service="S3", resource="mystery", purpose="")
        self.assertEqual([r.resource for r in ci.unattributed(self.ws)], ["mystery"])

    def test_resources_group_by_product_scope(self) -> None:
        self.add(resource="db-a", scope="denial")
        self.add(resource="db-b", scope="engagement")
        self.add(resource="ci", scope="")
        grouped = ci.by_scope(self.ws)
        self.assertEqual(set(grouped), {"denial", "engagement", "(platform)"})

    def test_summary_counts_what_needs_attention(self) -> None:
        old = (date.today() - timedelta(days=30)).isoformat()
        ci.add(self.ws, env="dev", provider="aws", service="ECS", resource="old", purpose="", created=old)
        ci.add(self.ws, env="prod", provider="aws", service="RDS", resource="db", purpose="live")
        data = ci.summary(self.ws)
        self.assertEqual(data["live"], 2)
        self.assertEqual(data["by_env"]["prod"], 1)
        self.assertEqual(data["unattributed"], 1)
        self.assertEqual(data["teardown"], 1)


if __name__ == "__main__":
    unittest.main()
