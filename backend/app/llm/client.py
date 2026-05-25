from __future__ import annotations

import json
import logging

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings
from app.llm.prompts import (
    EMAIL_SYSTEM_PROMPT,
    EMAIL_USER_PROMPT,
    SUMMARY_SYSTEM_PROMPT,
    SUMMARY_USER_PROMPT,
)
from app.models.schemas import ProfessorInput, StudentProfile

logger = logging.getLogger(__name__)


class ResearchSummary(BaseModel):
    summary: str = Field(min_length=1)
    main_research_area: str = Field(min_length=1)
    technical_problems: list[str] = Field(min_length=1, max_length=2)
    undergraduate_opportunity: str = Field(min_length=1)


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required.")
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)

    async def summarize_research(self, professor_name: str, research_text: str) -> ResearchSummary:
        user_prompt = SUMMARY_USER_PROMPT.format(
            professor_name=professor_name,
            research_text=research_text,
        )
        payload = await self._chat_json(
            model=self.settings.openai_model_summary,
            system_prompt=SUMMARY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        try:
            return ResearchSummary.model_validate(payload)
        except ValidationError as exc:
            logger.exception("Invalid summary payload from LLM: %s", payload)
            raise ValueError(f"Invalid summary payload from LLM: {exc}") from exc

    async def generate_email(
        self,
        student: StudentProfile,
        professor: ProfessorInput,
        summary: ResearchSummary,
        feedback: str | None = None,
        previous_email: str | None = None,
    ) -> str:
        regeneration_context = ""
        if feedback:
            regeneration_context = (
                f"Regeneration guidance:\n"
                f"- Previous draft:\n{previous_email or '(none)'}\n"
                f"- Improve based on this feedback:\n{feedback}\n"
            )

        user_prompt = EMAIL_USER_PROMPT.format(
            student_name=student.name,
            student_major=student.major,
            student_university=student.university,
            student_skills=", ".join(student.skills) if student.skills else "None listed",
            student_interests=", ".join(student.interests) if student.interests else "None listed",
            professor_name=professor.name,
            main_research_area=summary.main_research_area,
            technical_problems=", ".join(summary.technical_problems),
            undergrad_opportunity=summary.undergraduate_opportunity,
            summary=summary.summary,
            regeneration_context=regeneration_context,
        )
        payload = await self._chat_json(
            model=self.settings.openai_model_email,
            system_prompt=EMAIL_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=self.settings.openai_temperature,
        )
        email = str(payload.get("email", "")).strip()
        if not email:
            raise ValueError("LLM returned an empty email.")
        return email

    async def _chat_json(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> dict:
        try:
            response = await self.client.chat.completions.create(
                model=model,
                temperature=temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception as exc:
            logger.exception("OpenAI API call failed")
            raise RuntimeError(f"OpenAI API call failed: {exc}") from exc

        content = response.choices[0].message.content if response.choices else ""
        if not content:
            raise ValueError("LLM returned empty content.")
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            logger.exception("Failed to decode JSON from LLM content: %s", content)
            raise ValueError("LLM did not return valid JSON.") from exc

