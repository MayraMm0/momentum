from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models import User, Extracurricular
from backend.schemas import ExtracurricularCreate, ExtracurricularOut

router = APIRouter(prefix="/extracurriculars", tags=["extracurriculars"])


# ==== EXTRACURRICULAR CREATION ENDPOINT ====
@router.post("/add", response_model=ExtracurricularOut)
def add_extracurricular(
    extracurricular: ExtracurricularCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_extra = Extracurricular(
        user_id = current_user.id,
        **extracurricular.model_dump()
    )
    
    db.add(new_extra)
    db.commit()
    db.refresh(new_extra)
    
    return new_extra

# ==== LIST ACTIVE EXTRAS ENDPOINT ====
@router.get("/list", response_model=List[ExtracurricularOut])
def list_extracurriculars(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Extracurricular).filter(
        Extracurricular.user_id == current_user.id,
        Extracurricular.is_active == True
    ).all()
    
# ==== EXTRACURR TOGGLE ENDPOINT ====
@router.patch("/toggle/{extracurricular_id}", response_model=ExtracurricularOut)
def toggle_extracurricular(
    extracurricular_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    extra = db.query(Extracurricular).filter(
        Extracurricular.id == extracurricular_id,
        Extracurricular.user_id == current_user.id,
    ).first()
    
    if not extra:
        raise HTTPException(status_code=404, detail="Extracurricular not found")
    
    extra.is_active = not extra.is_active
    db.commit()
    db.refresh(extra)
    
    return extra