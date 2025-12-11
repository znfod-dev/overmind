"""Diary CRUD endpoints"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.diary.schemas.requests import GenerateDiaryRequest
from app.diary.schemas.responses import DiaryEntryResponse, DiaryListResponse
from app.diary.services.diary import DiaryService

router = APIRouter(prefix="/api/diaries", tags=["diaries"])


@router.post(
    "",
    response_model=DiaryEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate diary",
    description="Generate diary from conversation"
)
async def generate_diary(
    conversation_id: int = Query(..., description="Conversation ID to generate diary from"),
    request: GenerateDiaryRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DiaryEntryResponse:
    """
    Generate diary from conversation

    - Processes conversation messages
    - Calls AI to generate diary in specified length
    - Saves diary entry
    - Uses the entry_date from the conversation
    """
    service = DiaryService(db)
    diary = await service.generate_diary(
        user_id=current_user.id,
        conversation_id=conversation_id,
        title=request.title,
        length_type=request.length_type
    )

    return DiaryEntryResponse.model_validate(diary)


@router.get(
    "",
    response_model=DiaryListResponse,
    summary="List diaries",
    description="Get list of user's diary entries with optional date range filter"
)
async def list_diaries(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=100, description="Number of entries to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DiaryListResponse:
    """
    List diary entries

    - Optional date range filtering
    - Paginated results
    - Sorted by entry date (newest first)
    """
    # Parse dates
    start_date_obj = date.fromisoformat(start_date) if start_date else None
    end_date_obj = date.fromisoformat(end_date) if end_date else None

    service = DiaryService(db)
    entries, total = await service.list_diaries(
        user_id=current_user.id,
        start_date=start_date_obj,
        end_date=end_date_obj,
        limit=limit,
        offset=offset
    )

    return DiaryListResponse(
        entries=[DiaryEntryResponse.model_validate(e) for e in entries],
        total=total
    )


@router.get(
    "/date/{entry_date}",
    response_model=DiaryEntryResponse,
    summary="Get diary by date",
    description="Get diary entry for specific date"
)
async def get_diary_by_date(
    entry_date: str,  # YYYY-MM-DD
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DiaryEntryResponse:
    """Get diary for specific date"""
    try:
        date_obj = date.fromisoformat(entry_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

    service = DiaryService(db)
    diary = await service.get_diary_by_date(date_obj, current_user.id)

    return DiaryEntryResponse.model_validate(diary)


@router.get(
    "/{diary_id}",
    response_model=DiaryEntryResponse,
    summary="Get diary",
    description="Get specific diary entry by ID"
)
async def get_diary(
    diary_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DiaryEntryResponse:
    """Get specific diary entry"""
    service = DiaryService(db)
    diary = await service.get_diary(diary_id, current_user.id)

    return DiaryEntryResponse.model_validate(diary)


@router.delete(
    "/{diary_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete diary",
    description="Delete a diary entry"
)
async def delete_diary(
    diary_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete diary entry

    - Only owner can delete
    """
    service = DiaryService(db)
    await service.delete_diary(diary_id, current_user.id)
