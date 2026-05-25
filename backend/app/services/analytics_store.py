from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from app.models.schemas import AnalyticsRecord, AnalyticsResponse


class AnalyticsStore:
    def __init__(self) -> None:
        base_dir = Path(__file__).resolve().parents[2]
        self._data_dir = base_dir / "data"
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._file_path = self._data_dir / "analytics.json"
        self._lock = Lock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        if self._file_path.exists():
            return
        self._write({"records": []})

    def _read(self) -> dict:
        with self._lock:
            if not self._file_path.exists():
                return {"records": []}
            try:
                return json.loads(self._file_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {"records": []}

    def _write(self, payload: dict) -> None:
        with self._lock:
            self._file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _find_index(self, records: list[dict], draft_id: str) -> int | None:
        for idx, record in enumerate(records):
            if record.get("draft_id") == draft_id:
                return idx
        return None

    def create_record(
        self,
        draft_id: str,
        professor_name: str,
        professor_email: str,
        score: float,
    ) -> None:
        payload = self._read()
        records = payload.get("records", [])
        if self._find_index(records, draft_id) is not None:
            return

        now = datetime.now(timezone.utc).isoformat()
        records.append(
            {
                "draft_id": draft_id,
                "professor_name": professor_name,
                "professor_email": professor_email,
                "score": score,
                "status": "draft",
                "workflow_status": "draft",
                "response_status": "no_response",
                "sent_counted": False,
                "last_updated": now,
            }
        )
        payload["records"] = records
        self._write(payload)

    def update_workflow_status(self, draft_id: str, status: str, score: float | None = None) -> bool:
        payload = self._read()
        records = payload.get("records", [])
        idx = self._find_index(records, draft_id)
        if idx is None:
            return False

        record = records[idx]
        record["workflow_status"] = status
        if status == "sent":
            record["sent_counted"] = True
        response_status = record.get("response_status", "no_response")
        if response_status != "no_response":
            record["status"] = response_status
        else:
            record["status"] = status
        if score is not None:
            record["score"] = score
        record["last_updated"] = datetime.now(timezone.utc).isoformat()
        records[idx] = record
        payload["records"] = records
        self._write(payload)
        return True

    def update_response_status(self, draft_id: str, status: str) -> bool:
        payload = self._read()
        records = payload.get("records", [])
        idx = self._find_index(records, draft_id)
        if idx is None:
            return False

        record = records[idx]
        record["response_status"] = status
        if status == "no_response":
            record["status"] = record.get("workflow_status", "draft")
        else:
            record["status"] = status
        record["last_updated"] = datetime.now(timezone.utc).isoformat()
        records[idx] = record
        payload["records"] = records
        self._write(payload)
        return True

    def get_analytics(self) -> AnalyticsResponse:
        payload = self._read()
        raw_records = payload.get("records", [])
        records: list[AnalyticsRecord] = []
        approved = 0
        rejected = 0
        sent = 0
        responses = 0

        for raw in raw_records:
            workflow_status = raw.get("workflow_status", "draft")
            response_status = raw.get("response_status", "no_response")
            if workflow_status == "approved":
                approved += 1
            if workflow_status == "rejected":
                rejected += 1
            if raw.get("sent_counted", False):
                sent += 1
            if response_status == "responded":
                responses += 1

            last_updated = raw.get("last_updated") or datetime.now(timezone.utc).isoformat()
            records.append(
                AnalyticsRecord(
                    draft_id=raw.get("draft_id", ""),
                    professor_name=raw.get("professor_name", ""),
                    professor_email=raw.get("professor_email", "unknown@example.com"),
                    score=float(raw.get("score", 0)),
                    status=raw.get("status", "draft"),
                    response_status=response_status,
                    last_updated=datetime.fromisoformat(last_updated),
                )
            )

        total_generated = len(records)
        response_rate = round((responses / sent) * 100, 2) if sent > 0 else 0.0

        return AnalyticsResponse(
            total_generated=total_generated,
            approved=approved,
            rejected=rejected,
            sent=sent,
            responses=responses,
            response_rate=response_rate,
            records=records,
        )
