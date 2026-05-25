from __future__ import annotations

import asyncio
import logging

from app.core.config import Settings
from app.llm.client import LLMService
from app.models.schemas import (
    GenerateEmailsRequest,
    GeneratedEmailItem,
    ProfessorInput,
    StudentProfile,
)
from app.scraper.research_scraper import ResearchScraper
from app.services.analytics_store import AnalyticsStore
from app.services.personalization_validator import PersonalizationValidator
from app.services.review_store import ReviewStore

logger = logging.getLogger(__name__)


class EmailPipelineService:
    def __init__(
        self,
        settings: Settings,
        review_store: ReviewStore,
        analytics_store: AnalyticsStore,
    ) -> None:
        self.settings = settings
        self.review_store = review_store
        self.analytics_store = analytics_store
        self.scraper = ResearchScraper(settings)
        self.llm_service = LLMService(settings)
        self.validator = PersonalizationValidator()

    async def generate_emails(self, payload: GenerateEmailsRequest) -> list[GeneratedEmailItem]:
        semaphore = asyncio.Semaphore(3)

        async def _run(student: StudentProfile, professor: ProfessorInput) -> GeneratedEmailItem:
            async with semaphore:
                return await self._process_professor(student, professor)

        tasks = [_run(payload.student, professor) for professor in payload.professors]
        return await asyncio.gather(*tasks)

    async def _process_professor(
        self,
        student: StudentProfile,
        professor: ProfessorInput,
    ) -> GeneratedEmailItem:
        try:
            research_text = await self.scraper.extract_research_text(professor)
            summary_struct = await self.llm_service.summarize_research(professor.name, research_text)
            first_email = await self.llm_service.generate_email(student, professor, summary_struct)
            score_result = self.validator.score_email(first_email, summary_struct, professor.name)

            email_to_use = first_email
            final_score_result = score_result

            if score_result.score < 7:
                logger.info(
                    "Low score %.1f for %s. Regenerating once.",
                    score_result.score,
                    professor.name,
                )
                feedback_text = " ".join(score_result.feedback) or "Make the email more specific and natural."
                second_email = await self.llm_service.generate_email(
                    student=student,
                    professor=professor,
                    summary=summary_struct,
                    feedback=feedback_text,
                    previous_email=first_email,
                )
                second_score = self.validator.score_email(second_email, summary_struct, professor.name)
                if second_score.score >= score_result.score:
                    email_to_use = second_email
                    final_score_result = second_score

            status = "pending_review" if final_score_result.score >= 7 else "rejected"
            subject = f"Undergraduate Research Interest in {summary_struct.main_research_area.strip()}"

            draft = self.review_store.create_draft(
                professor_name=professor.name,
                professor_email=str(professor.email),
                student_name=student.name,
                summary_struct=summary_struct,
                summary_text=summary_struct.summary,
                subject=subject,
                email=email_to_use,
                score=final_score_result.score,
                status=status,
            )
            self.analytics_store.create_record(
                draft_id=draft.id,
                professor_name=draft.professor_name,
                professor_email=draft.professor_email,
                score=draft.score,
            )

            return GeneratedEmailItem(
                draft_id=draft.id,
                professor_name=draft.professor_name,
                professor_email=draft.professor_email,
                summary=draft.summary_text,
                email=draft.email,
                score=draft.score,
                status=draft.status,  # type: ignore[arg-type]
                subject=draft.subject,
                error=None,
            )
        except Exception as exc:
            logger.exception("Failed to generate email for %s", professor.name)
            return GeneratedEmailItem(
                draft_id="",
                professor_name=professor.name,
                professor_email=professor.email,
                summary="",
                email="",
                score=0,
                status="rejected",
                subject="",
                error=str(exc),
            )
