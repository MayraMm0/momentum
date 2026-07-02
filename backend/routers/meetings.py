from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models import User, Meeting
from backend.schemas import MeetingCreate, MeetingOut

router = APIRouter(prefix="/meetings", tags=["meetings"])

# ==== MEETING CREATION ENDPOINT ====
@router.post("/add", response_model=MeetingOut)
def add_meeting(
    meeting: MeetingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    new_meeting = Meeting(
        user_id = current_user.id,
        **meeting.model_dump()
    )
    
    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)
    
    return new_meeting

# ==== LIST ACTIVE MEETINGS ENDPOINT ====
@router.get("/list", response_model=List[MeetingOut])
def list_meetings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Meeting).filter(
        Meeting.user_id == current_user.id,
    ).all()
    
# ==== UPDATE MEETING INFO ENDPOINT ====
@router.patch("/update/{meeting_id}", response_model=MeetingOut)
def update_meeting(
    meeting_id: int,
    updates: MeetingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(meeting, field, value)
        
    db.commit()
    db.refresh(meeting)
    
    return meeting

# ==== DELETE MEETING ENDPOINT ====
#meetings don't have anything pointing at them (foreign keys)
# There's nothing that would break or become orphaned if a meeting row disappears -> simplet to hard delete
@router.delete("/delete/{meeting_id}")
def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user,)
):
    meeting = db.query(Meeting).filter(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id
    ).first()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    db.delete(meeting)
    db.commit()
    
    return {"message": f"Meeting '{meeting.title}' deleted"}