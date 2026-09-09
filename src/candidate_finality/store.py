from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .errors import Code, FinalityError
from .models import ExecutionHandle, ValidationReceipt, iso_z


class SQLiteFinalityStore:
    def __init__(self, path: str | Path = ":memory:") -> None:
        self._path = str(path)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self._path, isolation_level=None, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys=ON")
        if self._path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.executescript("""
        CREATE TABLE IF NOT EXISTS receipts (
          receipt_id TEXT PRIMARY KEY, act_id TEXT NOT NULL, hcad_digest TEXT NOT NULL,
          payload TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS handles (
          handle_id TEXT PRIMARY KEY, act_id TEXT NOT NULL, receipt_id TEXT NOT NULL REFERENCES receipts(receipt_id),
          hcad_digest TEXT NOT NULL, nonce TEXT NOT NULL UNIQUE, sink_id TEXT NOT NULL,
          state TEXT NOT NULL CHECK(state IN ('UNUSED','CONSUMED_PENDING','EFFECTUATED','FAILED_DEFINITE')),
          effect_id TEXT, payload TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS uq_effective_hcad ON handles(hcad_digest)
          WHERE state IN ('CONSUMED_PENDING','EFFECTUATED');
        """)

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                yield self._conn
            except Exception:
                self._conn.execute("ROLLBACK"); raise
            else:
                self._conn.execute("COMMIT")

    def commit_receipt(self, receipt: ValidationReceipt) -> None:
        with self._tx() as db:
            db.execute("INSERT INTO receipts VALUES (?, ?, ?, ?, ?)", (
                receipt.receipt_id, receipt.act_id, receipt.hcad_digest,
                json.dumps(receipt.to_dict(), sort_keys=True), iso_z(receipt.issued_at),
            ))

    def receipt(self, receipt_id: str) -> dict | None:
        row = self._conn.execute("SELECT payload FROM receipts WHERE receipt_id=?", (receipt_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def receipt_by_handle(self, handle_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT r.payload FROM receipts r JOIN handles h ON h.receipt_id=r.receipt_id WHERE h.handle_id=?",
            (handle_id,),
        ).fetchone()
        return json.loads(row[0]) if row else None


    def register_handle(self, handle: ExecutionHandle, receipt_id: str) -> None:
        with self._tx() as db:
            db.execute("INSERT INTO handles VALUES (?, ?, ?, ?, ?, ?, 'UNUSED', NULL, ?, ?)", (
                handle.handle_id, handle.act_id, receipt_id, handle.hcad_digest,
                handle.nonce, handle.sink_id, json.dumps(handle.to_dict(), sort_keys=True),
                iso_z(datetime.now(timezone.utc)),
            ))

    def reserve(self, handle_id: str, hcad_digest: str, sink_id: str) -> None:
        with self._tx() as db:
            row = db.execute("SELECT state, hcad_digest, sink_id FROM handles WHERE handle_id=?", (handle_id,)).fetchone()
            if row is None:
                raise FinalityError(Code.NO_HANDLE, "execution handle is not registered")
            if row["state"] != "UNUSED":
                raise FinalityError(Code.HANDLE_ALREADY_USED, f"handle state is {row['state']}")
            if row["hcad_digest"] != hcad_digest:
                raise FinalityError(Code.HCAD_MISMATCH, "registered HCAD digest differs")
            if row["sink_id"] != sink_id:
                raise FinalityError(Code.SINK_MISMATCH, "registered sink differs")
            try:
                changed = db.execute(
                    "UPDATE handles SET state='CONSUMED_PENDING', updated_at=? WHERE handle_id=? AND state='UNUSED'",
                    (iso_z(datetime.now(timezone.utc)), handle_id),
                ).rowcount
            except sqlite3.IntegrityError as exc:
                raise FinalityError(Code.REPLAY_DETECTED, "HCAD already consumed") from exc
            if changed != 1:
                raise FinalityError(Code.HANDLE_ALREADY_USED, "concurrent consume lost")

    def complete(self, handle_id: str, effect_id: str) -> None:
        with self._tx() as db:
            changed = db.execute(
                "UPDATE handles SET state='EFFECTUATED', effect_id=?, updated_at=? WHERE handle_id=? AND state='CONSUMED_PENDING'",
                (effect_id, iso_z(datetime.now(timezone.utc)), handle_id),
            ).rowcount
            if changed != 1:
                raise FinalityError(Code.FAIL_CLOSED, "handle was not reserved")

    def fail_definite(self, handle_id: str) -> None:
        with self._tx() as db:
            db.execute("UPDATE handles SET state='FAILED_DEFINITE', updated_at=? WHERE handle_id=? AND state='CONSUMED_PENDING'",
                       (iso_z(datetime.now(timezone.utc)), handle_id))

    def state(self, handle_id: str) -> str | None:
        row = self._conn.execute("SELECT state FROM handles WHERE handle_id=?", (handle_id,)).fetchone()
        return row[0] if row else None

    def close(self) -> None:
        self._conn.close()
