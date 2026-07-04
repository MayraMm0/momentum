from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models import User, Project
from backend.schemas import ProjectCreate, ProjectOut

router = APIRouter(prefix="/projects", tags=["projects"])

# ==== PROJECT CREATION ENDPOINT ====
@router.post("/add", response_model=ProjectOut)
def add_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_project = Project(
        user_id = current_user.id,
        **project.model_dump()
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return new_project


# ==== LIST ACTIVE PROJECTS ENDPOINT ====
@router.get("/list", response_model=List[ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Project).filter(
        Project.user_id == current_user.id,
        Project.status == "active"
    ).all()
    

# ==== UPDATE PROJECT INFO ENDPOINT ====
@router.patch("/update/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    updates: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
        
    db.commit()
    db.refresh(project)
    
    return project

# ==== MARK PROJECT COMPLETE ENDPOINT ====
@router.patch("/complete/{project_id}", response_model=ProjectOut)
def complete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.status = "completed"
    db.commit()
    db.refresh(project)

    return project

# ==== MARK PROJECT ARCHIVED ENDPOINT ====
@router.patch("/archive/{project_id}", response_model=ProjectOut)
def archive_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.status = "archived"
    db.commit()
    db.refresh(project)

    return project