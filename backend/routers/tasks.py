from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models import User, Task, NlpPrediction
from backend.schemas import TaskCreate, TaskUpdate, TaskOut, TaskWithPredictionOut
from backend.classifier import classify

router = APIRouter(prefix="/tasks", tags=["tasks"])

# ==== TASK CREATION ENDPOINT ====
@router.post("/add", response_model=TaskOut)
def add_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Run classifier on raw text
    result = classify(task.title, task.description)
    
    # 2. Resolve final values: user overrides or prediction
    final_type = task.type if task.type is not None else result.predicted_type.value
    final_subtype = task.subtype if task.subtype is not None else result.predicted_subtype
    
    # 3. Build Task with resolved values
    task_data = task.model_dump(exclude={"type", "subtype"})
    
    new_task = Task(
        user_id = current_user.id,
        type = final_type,
        subtype = final_subtype,
        **task_data
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    # 4. Write NlpPrediction, tracking whether user overrode
    prediction = NlpPrediction(
        task_id = new_task.id,
        predicted_type = result.predicted_type.value,
        predicted_subtype = result.predicted_subtype,
        confidence_score = result.confidence,
        model_version = result.model_version,
        user_overrode_type = (task.type is not None and task.type != result.predicted_type.value),
        user_overrode_subtype = (task.subtype is not None and task.subtype != result.predicted_subtype),
    )
    
    db.add(prediction)
    db.commit()
    
    return new_task

# ==== PLAIN LIST TASKS ENDPOINT ====
# Shows incompleted tasks
@router.get("/list", response_model=List[TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    return db.query(Task).filter(
        Task.user_id == current_user.id,
        Task.completed == False,
    ).all()
    
# ==== LIST TASKS & PREDICTION ENDPOINT ====
@router.get("/list/with-predictions", response_model= List[TaskWithPredictionOut])
def list_tasks_with_predictions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Task).options(
        joinedload(Task.nlp_prediction)
    ).filter(
        Task.user_id == current_user.id,
        Task.completed == False,
    ).all()
    
# ==== UPDATE TASK INFO ENDPOINT ====
@router.patch("/update/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    updates: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = updates.model_dump(exclude_unset=True)
    
    #If user overrides type or subtype we update override flag in NlpPrediction
    if "type" in update_data or "subtype" in update_data:
        prediction = db.query(NlpPrediction).filter(
            NlpPrediction.task_id == task.id
        ).first()
        
        if prediction:
            if "type" in update_data and update_data["type"] != prediction.predicted_type:
                prediction.user_overrode_type = True
            if "subtype" in update_data and update_data["subtype"] != prediction.predicted_subtype:
                prediction.user_overrode_subtype = True
                
    for field, value in update_data.items():
        setattr(task, field, value)
        
    db.commit()
    db.refresh(task)
    
    return task

# ==== TOGGLE TASK COMPLETION ENDPOINT ====
@router.patch("/complete/{task_id}", response_model=TaskOut)
def toggle_task_completion(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.completed = not task.completed
    db.commit()
    db.refresh(task)
    
    return task

# ==== TASK COMPLETION ENDPOINT ====
# Update for later: soft deletion to preserve NlpPrediction history (when we have analytics feature), task_id is non nullable on NlpPrediction
# Right now: we don't need it -> hard delete
@router.delete("/delete/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    prediction = db.query(NlpPrediction).filter(
        NlpPrediction.task_id == task.id
    ).first()
    
    if prediction: 
        db.delete(prediction)
        
    db.delete(task)
    db.commit()
    
    return {"message": f"Task deleted"}
    

