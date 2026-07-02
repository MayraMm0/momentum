from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import time
from typing import Optional

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
    model_config = ConfigDict(from_attribute = True)
    
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