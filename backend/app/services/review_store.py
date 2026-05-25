from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock

from app.llm.client import ResearchSummary


@dataclass
class DraftRecord:
    id: str
    professor_name: str
    professor_email: str
    student_name: str
    summary_struct: ResearchSummary
    summary_text: str
    subject: str
    email: str
    score: float
    status: str
    created_at: datetime
    updated_at: datetime
    message_id: str | None = None
    metadata: dict = field(default_factory=dict)


class ReviewStore:
    def __init__(self) -> None:
        self._drafts: dict[str, DraftRecord] = {}
        self._lock = Lock()

    def create_draft(
        self,
        professor_name: str,
        professor_email: str,
        student_name: str,
        summary_struct: ResearchSummary,
        summary_text: str,
        subject: str,
        email: str,
        score: float,
        status: str,
    ) -> DraftRecord:
        now = datetime.now(timezone.utc)
        record = DraftRecord(
            id=str(uuid.uuid4()),
            professor_name=professor_name,
            professor_email=professor_email,
            student_name=student_name,
            summary_struct=summary_struct,
            summary_text=summary_text,
            subject=subject,
            email=email,
            score=score,
            status=status,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._drafts[record.id] = record
        return record

    def get_draft(self, draft_id: str) -> DraftRecord | None:
        with self._lock:
            return self._drafts.get(draft_id)

    def update_review(
        self,
        draft_id: str,
        status: str,
        email: str | None = None,
        score: float | None = None,
    ) -> DraftRecord | None:
        with self._lock:
            draft = self._drafts.get(draft_id)
            if not draft:
                return None
            if email is not None:
                draft.email = email
            if score is not None:
                draft.score = score
            draft.status = status
            draft.updated_at = datetime.now(timezone.utc)
            return draft

    def mark_sent(self, draft_id: str, message_id: str, provider: str) -> DraftRecord | None:
        with self._lock:
            draft = self._drafts.get(draft_id)
            if not draft:
                return None
            draft.status = "sent"
            draft.message_id = message_id
            draft.metadata["provider"] = provider
            draft.updated_at = datetime.now(timezone.utc)
            return draft

