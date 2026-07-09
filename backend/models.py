from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time, Float, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
from backend.enums import TaskType, RecurrenceType

# back_populates on both sides of relationships make it navigable in both directions

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    degree = Column(String, default="general")
    gender = Column(String, default="neutral")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Everything where user is a foreign key
    sessions = relationship("Session", back_populates="user")
    courses = relationship("Course", back_populates="user")
    projects = relationship("Project", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    extracurriculars = relationship("Extracurricular", back_populates="user")
    meetings = relationship("Meeting", back_populates="user")
    motivation_logs = relationship("MotivationLog", back_populates="user")
    
class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sessions")

class Course(Base): 
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    canonical_name = Column(String, nullable=True)  # matched to daily_class_quotes at creation
    professor = Column(String, nullable=True)
    room = Column(String, nullable=True)
    days = Column(String, nullable=True)  # e.g. "MWF"
    time_start = Column(Time, nullable=True)
    time_end = Column(Time, nullable=True)
    semester = Column(String, nullable=True)  # e.g. "Fall 2026"
    difficulty_rank = Column(Integer, default=0)
    color_hex = Column(String, default="#7F77DD")
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="courses")
    tasks = relationship("Task", back_populates="course")
    projects = relationship("Project", back_populates="course")
    
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    deadline = Column(Date, nullable=True)
    status = Column(String, default="active")
    priority = Column(Integer, default=0)

    user = relationship("User", back_populates="projects")
    course = relationship("Course", back_populates="projects")
    tasks = relationship("Task", back_populates="project")

class Task(Base): 
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    type = Column(String, default=TaskType.ACADEMIC.value, nullable = False)
    subtype = Column(String, nullable=True)
    date_start = Column(DateTime, nullable=True)
    date_finish = Column(DateTime, nullable=True)
    has_deadline = Column(Boolean, default=True)
    estimated_hours = Column(Float, nullable=True)
    completed = Column(Boolean, default=False)
    priority_score = Column(Integer, default=0)
    location = Column(String, nullable=True)

    user = relationship("User", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    course = relationship("Course", back_populates="tasks")
    nlp_prediction = relationship("NlpPrediction", back_populates="task", uselist=False)


class Extracurricular(Base):
    __tablename__ = "extracurriculars"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    days = Column(String, nullable=True)
    time_start = Column(Time, nullable=True)
    time_end = Column(Time, nullable=True)
    location = Column(String, nullable=True)
    active_from = Column(Date, nullable=True)
    active_until = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="extracurriculars")

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    with_whom = Column(String, nullable=True)
    days = Column(String, nullable=True)
    time_start = Column(Time, nullable=True)
    time_end = Column(Time, nullable=True)
    location = Column(String, nullable=True)
    recurrence_type = Column(String, default=RecurrenceType.ONE_TIME.value)
    active_from = Column(Date, nullable=True)
    active_until = Column(Date, nullable=True)

    user = relationship("User", back_populates="meetings")

class NlpPrediction(Base):
    __tablename__ = "nlp_predictions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, unique = True, index = True)
    predicted_type = Column(String, nullable=False)
    predicted_subtype = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    user_overrode_type = Column(Boolean, default=False)
    user_overrode_subtype = Column(Boolean, default=False)
    model_version = Column(String, nullable=True)
    predicted_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="nlp_prediction")
    
class MotivationLog(Base):
    __tablename__ = "motivation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quote_text = Column(String, nullable=False)
    source = Column(String, nullable=True)
    trigger_context = Column(String, nullable=True)
    shown_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="motivation_logs")

