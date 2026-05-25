from __future__ import annotations

import logging
from functools import lru_cache

from fastapi import APIRouter, HTTPException, status

from app.core.config import Settings, get_settings
from app.models.schemas import (
    GenerateEmailsRequest,
    GenerateEmailsResponse,
    ProfessorInput,
    ReviewEmailRequest,
    ReviewEmailResponse,
    SendEmailRequest,
    SendEmailResponse,
    StudentProfile,
)
from app.services.email_pipeline import EmailPipelineService
from app.services.gmail_service import EmailSenderService
from app.services.personalization_validator import PersonalizationValidator
from app.services.review_store import ReviewStore
from app.routes.analytics_routes import get_analytics_store

logger = logging.getLogger(__name__)
sent_logger = logging.getLogger("sent_email")

router = APIRouter(tags=["cold-email"])


@lru_cache
def get_review_store() -> ReviewStore:
    return ReviewStore()


@lru_cache
def get_pipeline_service() -> EmailPipelineService:
    settings = get_settings()
    return EmailPipelineService(
        settings=settings,
        review_store=get_review_store(),
        analytics_store=get_analytics_store(),
    )


@lru_cache
def get_sender_service() -> EmailSenderService:
    settings = get_settings()
    return EmailSenderService(settings)


@lru_cache
def get_validator() -> PersonalizationValidator:
    return PersonalizationValidator()


@router.post("/generate_emails", response_model=GenerateEmailsResponse)
async def generate_emails(payload: GenerateEmailsRequest) -> GenerateEmailsResponse:
    # This endpoint requires POST, not GET.
    logger.info("generate_emails_requested professors=%d student=%s", len(payload.professors), payload.student.name)
    try:
        pipeline = get_pipeline_service()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline initialization failed: {exc}",
        ) from exc
    items = await pipeline.generate_emails(payload)
    logger.info("generate_emails_completed generated=%d", len(items))
    return GenerateEmailsResponse(items=items)


@router.get("/test_generate")
async def test_generate() -> dict:
    """
    Browser-friendly endpoint for quick smoke testing.
    Calls the same pipeline used by POST /generate_emails with hardcoded sample data.
    """
    sample_payload = GenerateEmailsRequest(
        student=StudentProfile(
            name="Alex Kim",
            major="Computer Science",
            university="State University",
            skills=["Python", "Machine Learning", "Data Analysis"],
            interests=["NLP", "Human-Centered AI"],
        ),
        professors=[
            ProfessorInput(
                name="Dr. Maya Chen",
                email="maya.chen@university.edu",
                research_text=(
                    "Our lab studies trustworthy NLP systems for clinical note understanding. "
                    "We focus on reducing hallucinations in summarization models and creating "
                    "evaluation frameworks for fairness across patient populations."
                ),
            )
        ],
    )

    logger.info("test_generate_requested")
    try:
        pipeline = get_pipeline_service()
        items = await pipeline.generate_emails(sample_payload)
    except Exception as exc:
        logger.exception("test_generate_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test generation failed: {exc}",
        ) from exc

    if not items:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No sample email was generated.",
        )

    logger.info("test_generate_completed")
    return {
        "message": "Sample generation complete",
        "sample": items[0].model_dump(),
    }


@router.post("/review_email", response_model=ReviewEmailResponse)
async def review_email(payload: ReviewEmailRequest) -> ReviewEmailResponse:
    review_store = get_review_store()
    draft = review_store.get_draft(payload.draft_id)
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Draft '{payload.draft_id}' not found.",
        )

    validator = get_validator()
    feedback: list[str] = []

    if payload.action == "reject":
        updated = review_store.update_review(draft_id=draft.id, status="rejected")
        if updated:
            get_analytics_store().update_workflow_status(updated.id, "rejected", score=updated.score)
    elif payload.action == "approve":
        if draft.score < 7:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Draft score is below 7. Edit before approving.",
            )
        updated = review_store.update_review(draft_id=draft.id, status="approved")
        if updated:
            get_analytics_store().update_workflow_status(updated.id, "approved", score=updated.score)
    else:  # action == "edit"
        score_result = validator.score_email(payload.edited_email or "", draft.summary_struct, draft.professor_name)
        feedback = score_result.feedback
        updated_status = "approved" if score_result.score >= 7 else "pending_review"
        updated = review_store.update_review(
            draft_id=draft.id,
            status=updated_status,
            email=payload.edited_email,
            score=score_result.score,
        )
        if updated:
            analytics_status = "approved" if updated.status == "approved" else "draft"
            get_analytics_store().update_workflow_status(updated.id, analytics_status, score=updated.score)

    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update draft.")

    return ReviewEmailResponse(
        draft_id=updated.id,
        professor_name=updated.professor_name,
        status=updated.status,  # type: ignore[arg-type]
        email=updated.email,
        score=updated.score,
        feedback=feedback,
        updated_at=updated.updated_at,
    )


@router.post("/send_email", response_model=SendEmailResponse)
async def send_email(payload: SendEmailRequest) -> SendEmailResponse:
    review_store = get_review_store()
    sender = get_sender_service()
    settings: Settings = get_settings()

    draft = review_store.get_draft(payload.draft_id)
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Draft '{payload.draft_id}' not found.",
        )
    if draft.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Draft must be approved before sending.",
        )

    provider = payload.provider or settings.email_provider
    try:
        message_id = await sender.send_email(
            to_email=draft.professor_email,
            subject=draft.subject,
            body=draft.email,
            provider=provider,
        )
    except Exception as exc:
        logger.exception("Failed to send email draft_id=%s", draft.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {exc}",
        ) from exc

    sent = review_store.mark_sent(draft.id, message_id, provider)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email sent but failed to update draft status.",
        )
    get_analytics_store().update_workflow_status(sent.id, "sent", score=sent.score)

    sent_logger.info(
        "sent draft_id=%s professor=%s to=%s provider=%s message_id=%s",
        sent.id,
        sent.professor_name,
        sent.professor_email,
        provider,
        message_id,
    )

    return SendEmailResponse(
        draft_id=sent.id,
        professor_name=sent.professor_name,
        status="sent",
        provider=provider,  # type: ignore[arg-type]
        message_id=message_id,
        sent_at=sent.updated_at,
    )
