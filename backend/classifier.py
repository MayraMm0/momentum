from dataclasses import dataclass
from typing import Optional
from backend.enums import TaskType

MODEL_VERSION = "rule-based-v0"

TYPE_CONFIDENCE_THRESHOLD = 0.5
SUBTYPE_CONFIDENCE_THRESHOLD = 0.6 # a single keyword match is enough to suggest subtype in this version

# Keyword -> TaskType -> subtype guess
# (e.g. "exam" matches TaskType.ACADEMIC and predicted_subtype = "exam").
# a REAL MODEL replaces this dict lookup later, the classify function will be the interface to the model

KEYWORD_MAP: dict[str, TaskType] = {
    # academic
    "exam": TaskType.ACADEMIC,
    "midterm": TaskType.ACADEMIC,
    "homework": TaskType.ACADEMIC,
    "quiz": TaskType.ACADEMIC,
    "assignment": TaskType.ACADEMIC,
    "reading": TaskType.ACADEMIC,
    "lecture": TaskType.ACADEMIC,
    "lab report": TaskType.ACADEMIC,
    "problem set": TaskType.ACADEMIC,
    # health
    "doctor": TaskType.HEALTH,
    "dentist": TaskType.HEALTH,
    "therapy": TaskType.HEALTH,
    "appointment": TaskType.HEALTH,
    "gym": TaskType.HEALTH,
    # social
    "party": TaskType.SOCIAL,
    "club": TaskType.SOCIAL,
    "meetup": TaskType.SOCIAL,
    "hangout": TaskType.SOCIAL,
    # personal
    "errand": TaskType.PERSONAL,
    "renew": TaskType.PERSONAL,
    "email": TaskType.PERSONAL,
    "call": TaskType.PERSONAL,
}

@dataclass
class ClassifierResult:
    predicted_type: TaskType
    predicted_subtype: Optional[str]
    confidence: float
    model_version: str
    
def classify(title: str, description: Optional[str]) -> ClassifierResult:
    """
    A simple rule-based classifier that uses keyword matching to predict the task type and subtype.
    Returns a ClassifierResult with the predicted type, subtype, confidence score, and model version.
    """
    
    text = f"{title} {description or ''}".lower()
    
    matches: list[tuple[str, TaskType]] = [
        (keyword, task_type)
        for keyword, task_type in KEYWORD_MAP.items()
        if keyword in text
    ]
    
    if not matches:
        # low confidence triggers fallback
        return ClassifierResult(
            predicted_type = TaskType.ACADEMIC,
            predicted_subtype=None,
            confidence=0.4,
            model_version=MODEL_VERSION,
        )
    
    # First match wins for type and subtype guess
    matched_keyword, matched_type = matches[0]
    confidence = min(0.5 + 0.1*len(matches), 0.9)
    
    predicted_type = matched_type if confidence >= TYPE_CONFIDENCE_THRESHOLD else TaskType.ACADEMIC
    predicted_subtype = matched_keyword if confidence >= SUBTYPE_CONFIDENCE_THRESHOLD else None
    
    return ClassifierResult(
        predicted_type=predicted_type,
        predicted_subtype=predicted_subtype,
        confidence=confidence,
        model_version=MODEL_VERSION,
    )