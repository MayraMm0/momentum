from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models import User, Course
from backend.schemas import CourseCreate, CourseOut

# prefix adds "/courses" to every route in the router
# tags is used by /docs to organize
router = APIRouter(prefix="/courses", tags=["courses"])

# ==== COURSE CREATION ENDPOINT ====
@router.post("/add", response_model=CourseOut)
def add_course(
    course: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_course = Course(
        user_id = current_user.id,
        # model_dump() converts a data model instance into a standard Python dictionary
        # "**" unpacks as keyword args directly into Course(...), without writing each field manually
        **course.model_dump()
    )
    
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    
    return new_course

# ==== LIST ACTIVE COURSES ENDPOINT ====
@router.get("/list", response_model=List[CourseOut])
def list_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Course).filter(
        Course.user_id == current_user.id,
        Course.is_active == True
    ).all()
    
# ==== UPDATE COURSE INFO ENDPOINT ====
@router.patch("/update/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int,
    updates: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
        
    db.commit()
    db.refresh(course)
    
    return course

# ==== COURSE DEACTIVATION ENDPOINT ====
@router.patch("/deactivate/{course_id}")
def deactivate_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course.is_active = False
    db.commit()
    
    return {"message": f"Course {course.name} deactivated"}

