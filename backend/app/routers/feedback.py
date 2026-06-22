from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.deps import get_current_user
from app.models.meeting import Meeting
from app.models.meeting_feedback import MeetingFeedback
from app.models.user import User
from app.schemas.feedback import MeetingFeedbackCreate, MeetingFeedbackRead

router = APIRouter(prefix="/v1/feedback", tags=["feedback"])


@router.post("/meeting", response_model=MeetingFeedbackRead)
def upsert_meeting_feedback(
    payload: MeetingFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MeetingFeedback:
    meeting = db.get(Meeting, payload.meeting_id)
    if not meeting or meeting.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Meeting not found")

    feedback = (
        db.query(MeetingFeedback)
        .filter(
            MeetingFeedback.user_id == current_user.id,
            MeetingFeedback.meeting_id == payload.meeting_id,
        )
        .first()
    )

    improvement_text = payload.improvement_text.strip() if payload.improvement_text else None
    if not improvement_text:
        improvement_text = None

    if feedback is None:
        feedback = MeetingFeedback(
            user_id=current_user.id,
            meeting_id=payload.meeting_id,
            usefulness=payload.usefulness,
            most_useful=payload.most_useful,
            improvement_text=improvement_text,
            would_use_again=payload.would_use_again,
            meeting_type=payload.meeting_type,
        )
    else:
        feedback.usefulness = payload.usefulness
        feedback.most_useful = payload.most_useful
        feedback.improvement_text = improvement_text
        feedback.would_use_again = payload.would_use_again
        feedback.meeting_type = payload.meeting_type

    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
