from __future__ import annotations

import io
import json
import re
from typing import Any

import fitz
from docx import Document
from openai import OpenAI

from app.core.config import Settings
from app.models.schemas import ResumeParseResponse

COMMON_SKILLS = {
    "python",
    "java",
    "c++",
    "c",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "node",
    "fastapi",
    "django",
    "flask",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "pandas",
    "numpy",
    "pytorch",
    "tensorflow",
    "scikit-learn",
    "git",
    "docker",
    "linux",
    "aws",
    "gcp",
    "azure",
}


class ResumeParserService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._llm_client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def parse_resume(self, filename: str, content: bytes) -> ResumeParseResponse:
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        if ext not in {"pdf", "docx", "txt"}:
            raise ValueError("Unsupported file type. Upload .pdf, .docx, or .txt.")

        if ext == "pdf":
            text = self._extract_pdf_text(content)
        elif ext == "docx":
            text = self._extract_docx_text(content)
        else:
            text = self._extract_txt_text(content)

        text = re.sub(r"\s+\n", "\n", text).strip()
        if not text:
            raise ValueError("The uploaded resume appears empty. Please upload a valid resume.")

        deterministic = self._deterministic_extract(text)
        if self._llm_client:
            llm_data = self._llm_extract(text)
            deterministic = self._merge_extraction(deterministic, llm_data)

        return ResumeParseResponse(**deterministic)

    @staticmethod
    def _extract_pdf_text(content: bytes) -> str:
        with fitz.open(stream=content, filetype="pdf") as doc:
            return "\n".join(page.get_text("text") for page in doc)

    @staticmethod
    def _extract_docx_text(content: bytes) -> str:
        document = Document(io.BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())

    @staticmethod
    def _extract_txt_text(content: bytes) -> str:
        return content.decode("utf-8", errors="ignore")

    def _deterministic_extract(self, text: str) -> dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        lowered = text.lower()

        name = self._extract_name(lines)
        university = self._extract_university(lines)
        major = self._extract_major(text)
        skills = self._extract_skills(lines, lowered)

        return {
            "name": name,
            "university": university,
            "major": major,
            "skills": skills,
        }

    def _extract_name(self, lines: list[str]) -> str | None:
        for line in lines[:8]:
            if "@" in line or any(char.isdigit() for char in line):
                continue
            parts = line.split()
            if 2 <= len(parts) <= 4 and all(part[:1].isalpha() for part in parts):
                return line
        return None

    def _extract_university(self, lines: list[str]) -> str | None:
        for line in lines:
            if re.search(r"\b(university|college|institute|school)\b", line, re.I):
                return line
        return None

    def _extract_major(self, text: str) -> str | None:
        patterns = [
            r"(?:major|majoring in)\s*[:\-]?\s*([A-Za-z &/]+)",
            r"(?:b\.?s\.?|bachelor(?:'s)?(?: of science)?)\s*(?:in)?\s*([A-Za-z &/]+)",
            r"(?:m\.?s\.?|master(?:'s)?)\s*(?:in)?\s*([A-Za-z &/]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip(" .,-")
        return None

    def _extract_skills(self, lines: list[str], lowered_text: str) -> list[str]:
        extracted: list[str] = []

        section_lines: list[str] = []
        in_skills_section = False
        for line in lines:
            if re.match(r"^skills?\b[:\-]?$", line, re.I):
                in_skills_section = True
                continue
            if in_skills_section and re.match(r"^[A-Z][A-Za-z ]{2,30}$", line) and " " not in line.strip("-• "):
                break
            if in_skills_section:
                section_lines.append(line)

        for line in section_lines:
            for chunk in re.split(r"[,|/;•]", line):
                cleaned = chunk.strip().strip("-")
                if cleaned:
                    extracted.append(cleaned)

        if not extracted:
            for skill in sorted(COMMON_SKILLS):
                if re.search(rf"\b{re.escape(skill)}\b", lowered_text, re.I):
                    extracted.append(skill)

        deduped: list[str] = []
        seen: set[str] = set()
        for skill in extracted:
            key = skill.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(skill)
        return deduped[:20]

    def _llm_extract(self, text: str) -> dict[str, Any]:
        if not self._llm_client:
            return {}
        prompt = (
            "Extract resume profile fields as strict JSON with keys: "
            "name, university, major, skills (array). Use null if missing."
        )
        try:
            response = self._llm_client.chat.completions.create(
                model=self.settings.openai_model_summary,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You extract structured resume data accurately."},
                    {"role": "user", "content": f"{prompt}\n\nResume text:\n{text[:12000]}"},
                ],
            )
            content = response.choices[0].message.content if response.choices else None
            if not content:
                return {}
            parsed = json.loads(content)
            return {
                "name": parsed.get("name"),
                "university": parsed.get("university"),
                "major": parsed.get("major"),
                "skills": parsed.get("skills") if isinstance(parsed.get("skills"), list) else [],
            }
        except Exception:
            return {}

    @staticmethod
    def _merge_extraction(primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
        merged = dict(primary)
        for key in ("name", "university", "major"):
            if not merged.get(key) and secondary.get(key):
                merged[key] = secondary[key]
        if not merged.get("skills") and secondary.get("skills"):
            merged["skills"] = secondary["skills"]
        return merged
