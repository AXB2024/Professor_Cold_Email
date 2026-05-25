from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.models.schemas import ResumeParseResponse
from app.services.resume_parser import ResumeParserService

router = APIRouter(prefix="", tags=["resume"])


@lru_cache
def get_resume_parser() -> ResumeParserService:
    return ResumeParserService(get_settings())


@router.post("/parse_resume", response_model=ResumeParseResponse)
async def parse_resume(file: UploadFile = File(...)) -> ResumeParseResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename in upload.")

    ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
    if ext not in {"pdf", "docx", "txt"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Upload .pdf, .docx, or .txt.",
        )

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    try:
        parser = get_resume_parser()
        return parser.parse_resume(file.filename, raw)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse resume: {exc}",
        ) from exc
