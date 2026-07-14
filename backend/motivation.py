# This file handles logic, separate from the endpoint
import re
import random
from openai import AsyncOpenAI
from difflib import SequenceMatcher
from typing import Optional
from datetime import date, datetime, time

from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_

from backend.config import settings
from backend.models import MotivationLog, User, Course, Task
from backend.constants import DAY_CODES
from backend.quotes.gender_degree import gender_degree_quotes
from backend.quotes.daily_classes import daily_class_quotes


RECENT_QUOTE_WINDOW = 20 # how many user's past quotes are cheked against

# ==== NORMALIZATION ====
# text normalization
def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # remove punctuation
    text = re.sub(r'\s+', ' ', text)     # collapse spaces
    return text.strip()

# degree normalization
# handles the case where degree comes in as a list and strips "engineering"
def normalize_degree(degree) -> str:
    if isinstance(degree, list):
        degree = degree[0] if degree else "neutral"
    
    degree = degree.lower().strip()
    if degree.endswith(" engineering"):
        degree = degree.rsplit(" engineering", 1)[0]
        
    return degree

# ==== SIMILARITIES CHECK ====

def is_similar(a: str, b: str, threshold: float = 0.85) -> bool:
    a_norm = normalize_text(a)
    b_norm = normalize_text(b)
    return SequenceMatcher(None, a_norm, b_norm).ratio() > threshold

# Fuzzy phrase check
def contains_fuzzy_phrase(text: str, phrase: str, threshold: float = 0.75) -> bool:
    text_norm = normalize_text(text)
    phrase_norm = normalize_text(phrase)
    len_phrase = len(phrase_norm) 
    # guard that prevents an empty phrase or a phrase longer than the text from causing an infinite loop or wrong results
    if len_phrase == 0 or len_phrase > len(text_norm):
        return False
    
    # Slide over text with windows matching phrase length
    for i in range(len(text_norm) - len_phrase + 1):
        window = text_norm[i:i+len_phrase]
        similarity = SequenceMatcher(None, window, phrase_norm).ratio()
        if similarity >= threshold:
            return True
    
    return False 

# ==== BANNED PHRASES ====
cliche_phrases = [ # banned phrases
    "reach for the stars",
    "the sky's the limit",
    "never give up",
    "dream big",
    "believe in yourself",
    "shoot for the stars"
    ]     

# ==== DB-BACKEND HISTORY CHECKS =====
# scoped per-user

def is_recent_duplicate(db: Session, user_id: int, candidate: str) -> bool:
    # True if candidate is too similar to a recently showed phrase
    recent = (
        db.query(MotivationLog).filter(
            MotivationLog.user_id == user_id
        ).order_by(
            desc(MotivationLog.shown_at)
        ).limit(
            RECENT_QUOTE_WINDOW
        ).all()
    )
    
    return any(is_similar(candidate, row.quote_text) for row in recent)

# Cliche check with banned phrases
def contains_recent_cliche(db: Session, user_id: int, candidate: str) -> bool:
    recent = (
        db.query(MotivationLog).filter(
            MotivationLog.user_id == user_id
        ).order_by(
            desc(MotivationLog.shown_at)
        ).limit(
            RECENT_QUOTE_WINDOW
        ).all()
    )
    
    for phrase in cliche_phrases:
        # If the candidate matches a cliche banned phrase
        if contains_fuzzy_phrase(candidate, phrase):
            # Check if that cliche appeared recently
            if any(contains_fuzzy_phrase(row.quote_text, phrase) for row in recent):
                return True
    
    # No recent cliche matched
    return False


# ==== DB USER INFO QUERIES ====

def get_hardest_class_today(db: Session, user_id: int) -> Optional[str]:
    today = date.today()
    day_code = DAY_CODES[today.weekday()]
    
    top_course = db.query(Course).filter(
        Course.user_id == user_id,
        Course.is_active == True,
        Course.days.contains(day_code),
    ).order_by(
        # SQLAlchemy's descending sort wrappe
        desc(Course.difficulty_rank)
    ).first()
    
    # No course scheduled today
    if top_course is None:
        return None
    
    # A course is scheduled but its canonical_name can be None (no matches)
    return top_course.canonical_name

def get_has_exam_today(db: Session, user_id: int) -> bool:
    today = date.today()
    
    # Builds 00:00:00 and 23:59:59 datetime objs for today
    start_of_day = datetime.combine(today, time.min)
    end_if_day = datetime.combine(today, time.max)
    
    possible_exam_subtypes = or_(
                Task.subtype.ilike("exam"), 
                Task.subtype.ilike("final"),
                Task.subtype.ilike("midterm"), 
                Task.subtype.ilike("quiz"), 
                Task.subtype.ilike("test")
            ),
    
    exam_task = (
        db.query(Task).filter(
            Task.user_id == user_id,
            possible_exam_subtypes,
            Task.completed == False,
            or_(
                # Date finish in range
                Task.date_finish.between(start_of_day, end_if_day),
                # or
                and_(
                    # date finish = None and date start today
                    Task.date_finish == None,
                    Task.date_start.between(start_of_day, end_if_day),
                ),
            ),
        ).first()
    )
    
    return exam_task is not None

# ==== GET STATIC QUOTES FROM FILES ====

# From gender_degree_quotes
def get_static_degree_quote(db: Session, user: User) -> str:
    user_degree_norm = normalize_degree(user.degree)
    
    matches = []
    # filters everything from quotes
    for q in gender_degree_quotes:
        quote_degrees = q["degree"]
        
        if isinstance(quote_degrees, str):
            # handles case where there is a list of degrees
            quote_degrees = [quote_degrees]
            
        # matches user's gender and normalized degree
        if (q["gender"] == user.gender or q["gender"] == "neutral") and (
            "neutral" in quote_degrees or user_degree_norm in quote_degrees
        ):
            matches.append(q)
    
    # shuffles the matches for randomness     
    random.shuffle(matches)
    
    # iterates until it finds one that passes recent duplicate and recent chliche filters
    for quote in matches:
        if not is_recent_duplicate(db, user.id, quote["text"]) and \
            not contains_recent_cliche(db, user.id, quote["text"]):
                return quote["text"]
            
    # falls back to a hardcoded string if nothing matches
    return "Keep going! Your effort matters."


# From class quotes
def get_static_class_quote(db: Session, user: User, canonical_class_name: str) -> str:
    user_degree_norm = normalize_degree(user.degree)
    
    matches = []
    for q in daily_class_quotes:
        class_field = q["class"]
        
        
        class_list = class_field if isinstance(class_field, list) else [class_field]
        # Checks if class name corresponds to current phrase or else skips it
        if canonical_class_name.lower() not in [c.lower() for c in class_list]:
            continue
        
        quote_degrees = q["degree"]
        if isinstance(quote_degrees, str):
            quote_degrees = [quote_degrees]
        
        # filters by gender and  degree
        if (q["gender"] == user.gender or q["gender"] == "neutral") and (
            "neutral" in quote_degrees or user_degree_norm in quote_degrees
        ):
            matches.append(q)
    
    random.shuffle(matches)
          
    # iterates until it finds one that passes recent duplicate and recent chliche filters
    for quote in matches:
        if not is_recent_duplicate(db, user.id, quote["text"]) and \
            not contains_recent_cliche(db, user.id, quote["text"]):
                return quote["text"]
    
    # falls back to a hardcoded string if nothing matches
    return f"Stay strong through {canonical_class_name} today!"
     
     
# ==== PROMPT GENERATION FOR GPT ====
# All functions just receive the values directly, they don't look them up (e.g. hardest class)

def generate_prompt_degree_gender(user: User) -> str:
    return (
        f"Generate a less than 20 words motivational quote for a {user.gender} student "
        f"majoring in {user.degree}. The quote should be original and inspiring."
    )

def generate_exam_prompt(user: User) -> str:
    return (
        f"Generate a less than 20 words quote for a {user.gender} student "
        f"who has an important exam today."
    )
    
def generate_prompt_daily_classes(user: User, hardest_class_today: str) -> str:
    return (
        f"Generate a less than 20 words quote for a {user.gender} student "
        f"whose most difficult class today is {hardest_class_today}."
    )
    
def generate_weekend_prompt() -> str:
    return (
        "Generate a less than 20 words quote for a college student on the weekend. "
        "Make it informal and optionally funny, encouraging rest or catching up on homework."
    )


# ==== GPT QUOTE GENERATION ====

# Async doesn't block program -> sends a request and allows code to run other tasks concurrently
aclient = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

AI_QUOTE_MODEL = "gpt-4o-mini"
AI_QUOTE_MAX_RETRIES = 4

# Suffixes list used as randomized style hints appended to prompts
_style_suffixes = [
    " Make it sound unique.",
    " Use a different tone than usual.",
    " Try a fresh perspective.",
    " Make it one-of-a-kind.",
    " Say it as if you were a friend encouraging someone.",
    " Use an analogy.",
    " Keep it casual.",
    " Talk like a personal trainer.",
    " Make him/her want to keep working hard."
]

# quote generation function
async def generate_ai_quote(db: Session, user: User, prompt: str) -> str:
    """
    Calls the OpenAI API to generate a quote, retrying with prompt variation
    if the result is a near-duplicate of something recently shown to this user.
    Raises the underlying OpenAI exception on real API failures — the caller
    (the /motivation endpoint) decides whether to fall back to a static quote.
    """
    
    last_attempt = None
    
    for _ in range(AI_QUOTE_MAX_RETRIES):
        varied_prompt = prompt + random.choice(_style_suffixes)
        response = await aclient.chat.completions.create(
            model=AI_QUOTE_MODEL,
            messages=[{"role": "user", "content": varied_prompt}],
            max_tokens = 40,
            temperature=0.9, # Higher temp pushes GPT toward more creative, varied responses
        )
        quote = response.choices[0].message.content.strip()
        last_attempt = quote
        
        if not is_recent_duplicate(db, user.id, quote) and \
            not contains_recent_cliche(db, user.id, quote):
                return quote
            
    # Every attempt was similar to a recent
    # return last one
    return last_attempt

# ==== LOGGING A SHOWN QOUTE ON DB ====
def record_shown_quote(db: Session, user_id: int, quote_text: str, source: str, trigger_context: str | None = None):
    log = MotivationLog(
        user_id = user_id,
        quote_text = quote_text,
        source = source,
        trigger_context = trigger_context,
    )
    
    db.add(log)
    db.commit()
    
    