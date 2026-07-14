from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, time, date, timedelta #span of time

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models import User, Course, Extracurricular, Meeting, Task
from backend.schemas import WeekResponse, DaySchedule
from backend.constants import DAY_CODES

router = APIRouter(tags=["schedule"])

@router.get("/schedule/week", response_model=WeekResponse)
def get_schedule_week(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Sunday -> Saturday boudary
    today = date.today()
    #In python Monday=0 Sunday=6
    #For calendar view Sunday=0 Saturday=6, we shift by 1 and wrap around
    days_since_sunday = (today.weekday() + 1) % 7
    week_start = today - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)

    days: list[DaySchedule] = []

    for i in range(7):
        current_day = week_start + timedelta(days=i)
        day_code = DAY_CODES[current_day.weekday()]
        
        courses = db.query(Course).filter(
            Course.user_id == current_user.id,
            Course.is_active == True,
            Course.days.contains(day_code),
        ).all()
        
        extracurriculars = db.query(Extracurricular).filter(
            Extracurricular.user_id == current_user.id,
            Extracurricular.is_active == True,
            Extracurricular.days.contains(day_code),
            or_(Extracurricular.active_from == None, Extracurricular.active_from <= current_day),
            or_(Extracurricular.active_until == None, Extracurricular.active_until >= current_day),
        ).all()
        
        meetings = db.query(Meeting).filter(
            Meeting.user_id == current_user.id,
            Meeting.days.contains(day_code),
            or_(Meeting.active_from == None, Meeting.active_from <= current_day),
            or_(Meeting.active_until == None, Meeting.active_until >= current_day),
        ).all()

        days.append(DaySchedule(
            date = current_day,
            courses = courses,
            extracurriculars = extracurriculars,
            meetings = meetings,
        ))
    
    week_end_inclusive = datetime.combine(week_end, time.max) # push boundary to end of Saturday
    
    tasks = db.query(Task).filter(
        Task.user_id == current_user.id,
        Task.completed == False,
        or_(
            Task.date_finish == None,
            Task.date_finish.between(week_start, week_end_inclusive),
        ),
    ).all()
    
    return WeekResponse(
        week_start = week_start,
        week_end = week_end,
        days = days,
        tasks = tasks,
    )