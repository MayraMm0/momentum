from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import time, date as date_type
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
