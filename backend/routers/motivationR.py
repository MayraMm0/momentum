import random
import openai
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models import User
from backend.enums import MotivationSource
from backend.schemas import MotivationOut
from backend.motivation import (
    get_hardest_class_today,
    get_has_exam_today,
    get_static_degree_quote,
    get_static_class_quote,
    generate_ai_quote,
    generate_prompt_degree_gender,
    generate_exam_prompt,
    generate_prompt_daily_classes,
    generate_weekend_prompt,
    record_shown_quote,
)

router = APIRouter(tags=["motivation"])

WEEKEND_FALLBACK = "Remember to include yourself in the list of things you need to take care of today."
EXAM_FALLBACK = "Good luck on your exam today!"

@router.get("/motivation", response_model=MotivationOut)
async def get_motivation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    is_weekend = today.weekday() in (5, 6)
    
    # ==== WEEKEND BRANCH ====
    if is_weekend:
        try:
            quote = await generate_ai_quote(db, current_user, generate_weekend_prompt())
        except openai.OpenAIError:
            quote = WEEKEND_FALLBACK
        record_shown_quote(db, current_user.id, quote, MotivationSource.AI_WEEKEND.value, "weekend") 
        return {"quote": quote}
    
    # ==== EXAM BRANCH ====
    if get_has_exam_today(db, current_user.id):
        try:
            quote = await generate_ai_quote(db, current_user, generate_exam_prompt(current_user))
        except openai.OpenAIError:
            quote = EXAM_FALLBACK
        record_shown_quote(db, current_user.id, quote, MotivationSource.AI_EXAM.value, "exam")
        return {"quote": quote}
    
    # ==== DEGREE vs CLASS BRANCH ====   
    hardest_class_today = get_hardest_class_today(db, current_user.id)
    
    # If class is None -> automatically do degree branch
    no_class_available = hardest_class_today is None
    use_class_branch = (not no_class_available) and (random.random() < 0.5) # random: 50% chance degree quote and 50% class quote
    
    # Degree branch
    if not use_class_branch:
        trigger_context = "degree:fallback_no_class" if no_class_available else f"degree:{current_user.degree}"
        
        if random.random() < 0.5: # 50% chance AI quote
            try:
                quote = await generate_ai_quote(db, current_user, generate_prompt_degree_gender(current_user))
                source = MotivationSource.AI_DEGREE.value
            except openai.OpenAIError:
                quote = get_static_degree_quote(db, current_user)
                source = MotivationSource.STATIC_DEGREE.value
        else: # 50% chance quote from file
            quote = get_static_degree_quote(db, current_user)
            source = MotivationSource.STATIC_DEGREE.value
    
    # Class branch      
    else: 
        trigger_context = f"class:{hardest_class_today}"
        class_chance = random.random()
        
        if class_chance < 0.5: # 50% chance AI quote
            try:
                quote = await generate_ai_quote(
                    db, current_user, generate_prompt_daily_classes(current_user, hardest_class_today)
                )
                source = MotivationSource.AI_CLASS.value
            except openai.OpenAIError:
                quote = get_static_class_quote(db, current_user, hardest_class_today)
                source = MotivationSource.STATIC_CLASS.value
        elif class_chance < 0.65: # 15% chance simple comment
            quote = "Good luck in today's classes!"
            source = MotivationSource.STATIC_CLASS.value
        elif class_chance < 0.80: # 15% chance simple comment targeting hardest class
            quote = f"Good luck with {hardest_class_today} today!"
            source = MotivationSource.STATIC_CLASS.value
        else: # 20% chance quote from file
            quote = get_static_class_quote(db, current_user, hardest_class_today)
            source = MotivationSource.STATIC_CLASS.value
            
    record_shown_quote(db, current_user.id, quote, source, trigger_context)
    return {"quote": quote}