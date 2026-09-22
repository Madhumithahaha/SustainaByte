"""Offline persistence and reconciliation tests using an isolated SQLite file."""

import tempfile
import unittest
from pathlib import Path

from auditor.architectures import SMALL_CNN
from auditor.lifecycle_math import Workload, calculate_lifecycle_impact
from auditor.offline_store import (
    get_pending_audits,
    get_pending_count,
    get_recent_audits,
    initialize_database,
    mark_audit_sync_failed,
    mark_audit_synced,
    save_audit,
    sync_pending_audits,
)


def sample_audit(name: str = "Small CNN") -> dict:
    return {
        "monthly_queries": 100_000,
        "architecture_name": name,
        "model_type": "cnn",
        "accuracy": 91.0,
        "latency_ms": 25.0,
        "energy": 12.5,
        "carbon": 5.0,
        "storage": 2.0,
        "networking": 3.0,
        "hardware": 0.5,
        "retraining": 1.0,
    }


class OfflineStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "offline.db"

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_persistence_queue_and_sync_lifecycle(self) -> None:
        self.assertTrue(initialize_database(self.path).exists())
        first = save_audit(sample_audit(), self.path)
        second = save_audit(sample_audit("Small Transformer"), self.path)
        self.assertNotEqual(first, second)
        self.assertEqual(get_pending_count(self.path), 2)
        self.assertEqual(len(get_pending_audits(self.path)), 2)
        mark_audit_sync_failed(first, self.path)
        self.assertEqual(get_pending_count(self.path), 2)
        mark_audit_synced(first, self.path)
        self.assertEqual(get_pending_count(self.path), 1)
        self.assertEqual(get_pending_audits(self.path)[0]["audit_id"], second)
        self.assertEqual(len(get_recent_audits(10, self.path)), 2)

    def test_demo_sync_is_idempotent_and_retains_offline_records(self) -> None:
        audit_id = save_audit(sample_audit(), self.path)
        offline = sync_pending_audits(online=False, db_path=self.path)
        self.assertFalse(offline["online"])
        self.assertEqual(get_pending_count(self.path), 1)
        online = sync_pending_audits(online=True, db_path=self.path)
        self.assertEqual(online["synced"], 1)
        self.assertEqual(online["target"], "local_demo_sink")
        self.assertEqual(get_pending_count(self.path), 0)
        self.assertEqual(get_recent_audits(1, self.path)[0]["audit_id"], audit_id)

    def test_local_lifecycle_calculation_needs_no_network(self) -> None:
        impact = calculate_lifecycle_impact(SMALL_CNN, Workload(inference_count=10))
        self.assertIn("energy", impact)
        self.assertIn("retraining", impact)


if __name__ == "__main__":
    unittest.main()
