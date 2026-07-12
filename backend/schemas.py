from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime, time, date as date_type
from typing import Optional, List

# What the client sends
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    degree: str = "general"
    gender: str = "neutral"
    
# What the server sends back (we avoid sending a password hash)
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes = True) # lets this read directly from a SQLAlchemy object
    id:int
    username: str
    email: str
    degree: str
    gender: str

# What user sends when logging in          
class LoginRequest(BaseModel):
    username: str
    password: str
# What server sends when login successful
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
    
# Creating a course
class CourseCreate(BaseModel):
    name: str
    professor: Optional[str] = None
    room: Optional[str] = None
    days: Optional[str] = None    # e.g. "MWF"
    time_start: Optional[time] = None
    time_end: Optional[time] = None
    semester: Optional[str] = None
    difficulty_rank: int = 0
    color_hex: str = "#7F77DD"
    
# Sends back course data
class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes = True)
    
    id: int
    user_id: int
    name: str
    canonical_name: Optional[str] = None
    professor: Optional[str] = None
    room: Optional[str] = None
    days: Optional[str] = None
    time_start: Optional[time] = None
    time_end: Optional[time] = None
    semester: Optional[str] = None
    difficulty_rank: int
    color_hex: str
    is_active: bool
    
# Creating an extracurricular activity
class ExtracurricularCreate(BaseModel):
    name: str
    days: Optional[str] = None
    time_start: Optional[time] = None
    time_end: Optional[time] = None
    location: Optional[str] = None
    active_from: Optional[date_type] = None
    active_until: Optional[date_type] = None

# Sends back extracurricular data
class ExtracurricularOut(BaseModel):
    model_config = ConfigDict(from_attributes = True)
    
    id: int
    user_id: int
    name: str
    days: Optional[str] = None
    time_start: Optional[time] = None
    time_end: Optional[time] = None
    location: Optional[str] = None
    active_from: Optional[date_type] = None
    active_until: Optional[date_type] = None
    is_active: bool
    
# Creating a meeting
class MeetingCreate(BaseModel):
    title: str
    with_whom: Optional[str] = None
    days: Optional[str] = None
    time_start: Optional[time] = None
    time_end: Optional[time] = None
    location: Optional[str] = None
    recurrence_type: str = "one_time"
    active_from: Optional[date_type] = None
    active_until: Optional[date_type] = None

class MeetingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    title: str
    with_whom: Optional[str] = None
    days: Optional[str] = None
    time_start: Optional[time] = None
    time_end: Optional[time] = None
    location: Optional[str] = None
    recurrence_type: str = "one_time"
    active_from: Optional[date_type] = None
    active_until: Optional[date_type] = None
    
# Every event for Today (response)
class TodayResponse(BaseModel):
    date: date_type
    courses: List[CourseOut] = []
    extracurriculars: List[ExtracurricularOut] = []
    meetings: List[MeetingOut] = []

# Creating a Project
class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    course_id: Optional[int] = None
    deadline: Optional[date_type] = None
    priority: int = 0
    
# Sends back project data
class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes = True)
    
    id: int
    user_id: int
    course_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    deadline: Optional[date_type] = None
    status: str
    priority: int
    
# NLP Prediction (only nested inside another response, never alone)
class NlpPredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes= True)
    
    predicted_type: str
    predicted_subtype: Optional[str] = None
    confidence_score: Optional[float] = None
    user_overrode_type: bool
    user_overrode_subtype: bool
    model_version: Optional[str] = None
    
# Creating a task
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: Optional[int] = None
    course_id: Optional[int] = None
    type: Optional[str] = None      # client can override classifier, kept it as str so the router is the single place that decides what "valid type" means
    subtype: Optional[str] = None   # client can override classifier
    date_start: Optional[datetime] = None
    date_finish: Optional[datetime] = None
    has_deadline: bool = True
    estimated_hours: Optional[float] = None
    location: Optional[str] = None

# Updating a task
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[int] = None
    course_id: Optional[int] = None
    type: Optional[str] = None
    subtype: Optional[str] = None
    date_start: Optional[datetime] = None
    date_finish: Optional[datetime] = None
    has_deadline: Optional[bool] = None
    estimated_hours: Optional[float] = None
    location: Optional[str] = None

    
# Plain task output
class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    project_id: Optional[int] = None
    course_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    type: str
    subtype: Optional[str] = None
    date_start: Optional[datetime] = None
    date_finish: Optional[datetime] = None
    has_deadline: bool
    estimated_hours: Optional[float] = None
    completed: bool
    priority_score: Optional[int] = None
    location: Optional[str] = None

# Task + NLP Prediction
class TaskWithPredictionOut(TaskOut):
        nlp_prediction: Optional[NlpPredictionOut] = None
        
# One day calendar grid info (courses/extracurriculars/meetings only — no tasks)
class DaySchedule(BaseModel):
    date: date_type
    courses: List[CourseOut] = []
    extracurriculars: List[ExtracurricularOut] = []
    meetings: List[MeetingOut] = []
    
# Full week view
class WeekResponse(BaseModel):
    week_start: date_type # Sunday
    week_end: date_type   # Saturday}
    days: List[DaySchedule] = []
    tasks: List[TaskOut] = []
    
class MotivationOut(BaseModel):
    quote: str