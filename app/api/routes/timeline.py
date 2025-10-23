from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import TimelineEvent
from app.schemas.entities import TimelineEvent as TimelineEventSchema

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/", response_model=List[TimelineEventSchema])
async def list_timeline_events(
    application_id: int,
    db: Session = Depends(get_db),
    __: None = Depends(get_current_user),
) -> List[TimelineEvent]:
    return (
        db.query(TimelineEvent)
        .filter(TimelineEvent.application_id == application_id)
        .order_by(TimelineEvent.created_at.desc())
        .all()
    )
