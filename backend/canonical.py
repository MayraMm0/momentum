from difflib import SequenceMatcher
from typing import Optional
from backend.quotes.daily_classes import daily_class_quotes

MATCH_THRESHOLD = 0.6

def _normalize(text: str) -> str:
    return text.lower().strip()

def _get_canonical_class_names() -> list[str]:
    # Flatten daily_class_quotes 'class' field (str or list) into a unique values set
    names = set()
    
    for q in daily_class_quotes:
        class_field = q["class"]
        if isinstance(class_field, list):
            names.update(class_field)
        else:
            names.add(class_field)
            
    return sorted(names)

# Computed once at import time, not on every call (quote bank doesn't change at runtime)
CANONICAL_CLASS_NAMES = _get_canonical_class_names()

def match_canonical_name(course_name: str) -> Optional[str]:
    if not course_name:
        return None
    
    normalized_input = _normalize(course_name)
    best_match = None
    best_score = 0.0
    
    for canonical in CANONICAL_CLASS_NAMES:
        # Finds longest matching contiguous blocks between two strings, recursively
        # sums up total matched chars (M), returns 2*M / combined_len_strings
        score = SequenceMatcher(None, normalized_input, _normalize(canonical)).ratio()
        if score > best_score:
            best_score = score
            best_match = canonical
            
    return best_match if best_score >= MATCH_THRESHOLD else None
        
