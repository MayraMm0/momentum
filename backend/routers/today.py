from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, date

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models import User, Course, Extracurricular, Meeting
from backend.schemas import TodayResponse

router = APIRouter(tags=["today"])

DAY_CODES = {
    0: "M",
    1: "T",
    2: "W",
    3: "R",
    4: "F",
    5: "S",
    6: "U",
}

@router.get("/today", response_model=TodayResponse)
def get_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    day_code = DAY_CODES[today.weekday()]
    
    courses = db.query(Course).filter(
        Course.user_id == current_user.id,
        Course.is_active == True,
        Course.days.contains(day_code),
    ).all()
    
    extracurriculars = db.query(Extracurricular).filter(
        Extracurricular.user_id == current_user.id,
        Extracurricular.is_active == True,
        Extracurricular.days.contains(day_code),
        or_(Extracurricular.active_from == None, Extracurricular.active_from <= today),
        or_(Extracurricular.active_until == None, Extracurricular.active_until >= today),
    ).all()
    
    meetings = db.query(Meeting).filter(
        Meeting.user_id == current_user.id,
        Meeting.days.contains(day_code),
        or_(Meeting.active_from == None, Meeting.active_from <= today),
        or_(Meeting.active_until == None, Meeting.active_until >= today),
    ).all()
    
    return TodayResponse(
        date = today,
        courses = courses,
        extracurriculars = extracurriculars,
        meetings = meetings,
    )