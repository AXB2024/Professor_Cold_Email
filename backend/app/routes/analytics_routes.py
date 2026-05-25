from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    AnalyticsResponse,
    AnalyticsStatusUpdateRequest,
    AnalyticsStatusUpdateResponse,
)
from app.services.analytics_store import AnalyticsStore

router = APIRouter(prefix="", tags=["analytics"])


@lru_cache
def get_analytics_store() -> AnalyticsStore:
    return AnalyticsStore()


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics() -> AnalyticsResponse:
    return get_analytics_store().get_analytics()


@router.post("/analytics/update_status", response_model=AnalyticsStatusUpdateResponse)
async def update_analytics_status(payload: AnalyticsStatusUpdateRequest) -> AnalyticsStatusUpdateResponse:
    updated = get_analytics_store().update_response_status(payload.draft_id, payload.status)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analytics record for draft '{payload.draft_id}' was not found.",
        )
    return AnalyticsStatusUpdateResponse(
        draft_id=payload.draft_id,
        status=payload.status,
        message="Status updated",
    )
