from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, HttpUrl, model_validator


class StudentProfile(BaseModel):
    name: str = Field(min_length=1)
    major: str = Field(min_length=1)
    university: str = Field(min_length=1)
    skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)


class ProfessorInput(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    research_text: str | None = None
    website_url: HttpUrl | None = None

    @model_validator(mode="after")
    def validate_research_source(self) -> "ProfessorInput":
        if not self.research_text and not self.website_url:
            raise ValueError("Either research_text or website_url must be provided.")
        return self


class GenerateEmailsRequest(BaseModel):
    student: StudentProfile
    professors: list[ProfessorInput] = Field(min_length=1)


class GeneratedEmailItem(BaseModel):
    draft_id: str
    professor_name: str
    professor_email: EmailStr
    summary: str
    email: str
    score: float = Field(ge=0, le=10)
    status: Literal["pending_review", "approved", "rejected", "sent"]
    subject: str
    error: str | None = None


class GenerateEmailsResponse(BaseModel):
    items: list[GeneratedEmailItem]


class ReviewEmailRequest(BaseModel):
    draft_id: str
    action: Literal["approve", "edit", "reject"]
    edited_email: str | None = None

    @model_validator(mode="after")
    def validate_edit_content(self) -> "ReviewEmailRequest":
        if self.action == "edit" and not self.edited_email:
            raise ValueError("edited_email is required when action is 'edit'.")
        return self


class ReviewEmailResponse(BaseModel):
    draft_id: str
    professor_name: str
    status: Literal["pending_review", "approved", "rejected", "sent"]
    email: str
    score: float = Field(ge=0, le=10)
    feedback: list[str] = Field(default_factory=list)
    updated_at: datetime


class SendEmailRequest(BaseModel):
    draft_id: str
    provider: Literal["smtp", "gmail_api"] | None = None


class SendEmailResponse(BaseModel):
    draft_id: str
    professor_name: str
    status: Literal["sent"]
    provider: Literal["smtp", "gmail_api"]
    message_id: str
    sent_at: datetime


class ResumeParseResponse(BaseModel):
    name: str | None = None
    university: str | None = None
    major: str | None = None
    skills: list[str] = Field(default_factory=list)


class AnalyticsRecord(BaseModel):
    draft_id: str
    professor_name: str
    professor_email: EmailStr
    score: float = Field(ge=0, le=10)
    status: Literal["draft", "approved", "rejected", "sent", "responded", "no_response", "follow_up_needed"]
    response_status: Literal["no_response", "responded", "follow_up_needed"] = "no_response"
    last_updated: datetime


class AnalyticsResponse(BaseModel):
    total_generated: int
    approved: int
    rejected: int
    sent: int
    responses: int
    response_rate: float
    records: list[AnalyticsRecord] = Field(default_factory=list)


class AnalyticsStatusUpdateRequest(BaseModel):
    draft_id: str
    status: Literal["no_response", "responded", "follow_up_needed"]


class AnalyticsStatusUpdateResponse(BaseModel):
    draft_id: str
    status: Literal["no_response", "responded", "follow_up_needed"]
    message: str
