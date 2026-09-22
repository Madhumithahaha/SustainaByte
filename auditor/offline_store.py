"""Persistent offline audit queue and optional synchronization abstraction."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

from .connectivity import is_internet_available


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "sustainabyte_offline.db"

_AUDIT_COLUMNS = (
    "audit_id", "timestamp", "monthly_queries", "architecture_name", "model_type",
    "accuracy", "latency_ms", "energy", "carbon", "storage", "networking",
    "hardware", "retraining", "sync_status", "created_at",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _database_path(db_path: Optional[Path | str]) -> Path:
    return Path(db_path) if db_path is not None else DEFAULT_DATABASE_PATH


@contextmanager
def _connect(db_path: Optional[Path | str] = None):
    path = _database_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database(db_path: Optional[Path | str] = None) -> Path:
    """Create the persistent audit queue and idempotent demo-sync receipt table."""
    path = _database_path(db_path)
    with _connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                monthly_queries INTEGER NOT NULL,
                architecture_name TEXT NOT NULL,
                model_type TEXT,
                accuracy REAL,
                latency_ms REAL,
                energy REAL,
                carbon REAL,
                storage REAL,
                networking REAL,
                hardware REAL,
                retraining REAL,
                sync_status TEXT NOT NULL DEFAULT 'pending',
                sync_attempts INTEGER NOT NULL DEFAULT 0,
                last_sync_attempt TEXT,
                synced_at TEXT,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_audits_pending ON audits(sync_status, created_at);
            CREATE TABLE IF NOT EXISTS demo_sync_receipts (
                audit_id TEXT PRIMARY KEY,
                received_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            """
        )
    return path


def save_audit(audit: Mapping[str, Any], db_path: Optional[Path | str] = None) -> str:
    """Persist one architecture's locally calculated audit before any sync attempt."""
    initialize_database(db_path)
    timestamp = str(audit.get("timestamp") or _now())
    audit_id = str(audit.get("audit_id") or f"audit-{uuid.uuid4()}")
    values = {
        "audit_id": audit_id,
        "timestamp": timestamp,
        "monthly_queries": int(audit["monthly_queries"]),
        "architecture_name": str(audit["architecture_name"]),
        "model_type": audit.get("model_type"),
        "accuracy": audit.get("accuracy"),
        "latency_ms": audit.get("latency_ms"),
        "energy": audit.get("energy"),
        "carbon": audit.get("carbon"),
        "storage": audit.get("storage"),
        "networking": audit.get("networking"),
        "hardware": audit.get("hardware"),
        "retraining": audit.get("retraining"),
        "sync_status": "pending",
        "created_at": str(audit.get("created_at") or timestamp),
    }
    placeholders = ", ".join(f":{column}" for column in _AUDIT_COLUMNS)
    with _connect(db_path) as connection:
        connection.execute(
            f"INSERT INTO audits ({', '.join(_AUDIT_COLUMNS)}) VALUES ({placeholders})",
            values,
        )
    return audit_id


def _rows(query: str, values: tuple[Any, ...] = (), db_path: Optional[Path | str] = None) -> list[dict[str, Any]]:
    initialize_database(db_path)
    with _connect(db_path) as connection:
        return [dict(row) for row in connection.execute(query, values).fetchall()]


def get_pending_audits(db_path: Optional[Path | str] = None) -> list[dict[str, Any]]:
    return _rows("SELECT * FROM audits WHERE sync_status = 'pending' ORDER BY created_at, id", db_path=db_path)


def get_pending_count(db_path: Optional[Path | str] = None) -> int:
    initialize_database(db_path)
    with _connect(db_path) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM audits WHERE sync_status = 'pending'").fetchone()[0])


def get_recent_audits(limit: int = 8, db_path: Optional[Path | str] = None) -> list[dict[str, Any]]:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer.")
    return _rows("SELECT * FROM audits ORDER BY created_at DESC, id DESC LIMIT ?", (limit,), db_path)


def mark_audit_synced(audit_id: str, db_path: Optional[Path | str] = None) -> None:
    now = _now()
    with _connect(db_path) as connection:
        connection.execute(
            "UPDATE audits SET sync_status = 'synced', sync_attempts = sync_attempts + 1, last_sync_attempt = ?, synced_at = ? WHERE audit_id = ?",
            (now, now, audit_id),
        )


def mark_audit_sync_failed(audit_id: str, db_path: Optional[Path | str] = None) -> None:
    with _connect(db_path) as connection:
        connection.execute(
            "UPDATE audits SET sync_status = 'pending', sync_attempts = sync_attempts + 1, last_sync_attempt = ? WHERE audit_id = ?",
            (_now(), audit_id),
        )


def _sync_to_remote(audit: Mapping[str, Any], endpoint: str) -> None:
    payload = json.dumps(dict(audit), default=str).encode("utf-8")
    request = Request(endpoint, data=payload, headers={"Content-Type": "application/json", "Idempotency-Key": str(audit["audit_id"])}, method="POST")
    with urlopen(request, timeout=2.0) as response:
        if not 200 <= response.status < 300:
            raise URLError(f"sync endpoint returned HTTP {response.status}")


def _sync_to_demo_sink(audit: Mapping[str, Any], db_path: Optional[Path | str]) -> None:
    """Durably reconcile to an explicitly local demo target when no backend exists."""
    with _connect(db_path) as connection:
        connection.execute(
            "INSERT OR IGNORE INTO demo_sync_receipts (audit_id, received_at, payload_json) VALUES (?, ?, ?)",
            (audit["audit_id"], _now(), json.dumps(dict(audit), default=str, sort_keys=True)),
        )


def sync_pending_audits(*, online: Optional[bool] = None, db_path: Optional[Path | str] = None) -> dict[str, Any]:
    """Reconcile pending records without ever deleting an unsynchronized audit.

    ``SUSTAINABYTE_SYNC_URL`` selects a real HTTP endpoint. Without it, this
    uses the clearly labelled local demo sink for an offline-feature demo.
    """
    connected = is_internet_available() if online is None else online
    pending = get_pending_audits(db_path)
    result = {"online": connected, "attempted": 0, "synced": 0, "failed": 0, "target": "remote" if os.getenv("SUSTAINABYTE_SYNC_URL") else "local_demo_sink"}
    if not connected:
        return result
    endpoint = os.getenv("SUSTAINABYTE_SYNC_URL")
    for audit in pending:
        result["attempted"] += 1
        try:
            if endpoint:
                _sync_to_remote(audit, endpoint)
            else:
                _sync_to_demo_sink(audit, db_path)
            mark_audit_synced(audit["audit_id"], db_path)
            result["synced"] += 1
        except (OSError, URLError, ValueError, sqlite3.Error):
            mark_audit_sync_failed(audit["audit_id"], db_path)
            result["failed"] += 1
    return result
