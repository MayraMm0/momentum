from datetime import date as real_date
from unittest.mock import patch, AsyncMock, MagicMock
import openai
from backend.models import MotivationLog

MODULE = "backend.routers.motivationR"

# fixed wednesday, so is_weekend is always False
FIXED_WEEKDAY = real_date(2026, 7, 8)

def _mock_date():
    """Returns a MagicMock standing in for the `date` class, with `.today()`
    patched to a fixed weekday."""
    # any attribute access not explicitly overridden falls through to the real date class instead of returning a generic Mock object
    mock = MagicMock(wraps=real_date)
    mock.today.return_value = FIXED_WEEKDAY
    return mock

def _mock_date_for(fixed_date):
    """Same idea as _mock_date(), but for a caller-specified date rather than the hardcoded Wednesday."""
    mock = MagicMock(wraps=real_date)
    mock.today.return_value = fixed_date
    return mock

# Auth guard endpoint
def test_motivation_endpoint_requites_authentication(client):
    response = client.get("/motivation")
    
    assert response.status_code == 401
  
# Response shape matches MotivaionOut  
def test_response_shape_matches_motivation_out(client, auth_headers):
    with patch(f"{MODULE}.date", new=_mock_date()), \
         patch(f"{MODULE}.get_has_exam_today", return_value=False), \
         patch(f"{MODULE}.get_hardest_class_today", return_value=None), \
         patch(f"{MODULE}.random.random", return_value=0.1), \
         patch(f"{MODULE}.get_static_degree_quote", return_value="static degree quote"):
        response = client.get("/motivation", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"quote"}
    assert isinstance(data["quote"], str)
    
# MotivationLog created after successful call
def test_motivation_log_row_created_on_success(client, auth_headers, db_session):
    with patch(f"{MODULE}.date", new=_mock_date()), \
         patch(f"{MODULE}.get_has_exam_today", return_value=False), \
         patch(f"{MODULE}.get_hardest_class_today", return_value=None), \
         patch(f"{MODULE}.random.random", return_value=0.9), \
         patch(f"{MODULE}.get_static_degree_quote", return_value="static degree quote"):
        response = client.get("/motivation", headers=auth_headers)

    assert response.status_code == 200

    log = db_session.query(MotivationLog).order_by(MotivationLog.id.desc()).first()
    assert log is not None
    assert log.quote_text == "static degree quote"
    assert log.source is not None
    assert log.trigger_context is not None
    assert log.shown_at is not None
    
# Weekend -> AI -> source=AI_WEEKEND, trigger_context="weekend"
def test_weekend_uses_ai_weekend_quote(client, auth_headers, db_session):
    saturday = real_date(2026, 7, 11)  # a real Saturday
    with patch(f"{MODULE}.date", new=_mock_date_for(saturday)), \
         patch(f"{MODULE}.generate_ai_quote", new_callable=AsyncMock, return_value="ai weekend quote"):
        response = client.get("/motivation", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["quote"] == "ai weekend quote"

    log = db_session.query(MotivationLog).order_by(MotivationLog.id.desc()).first()
    assert log.source == "ai_weekend"
    assert log.trigger_context == "weekend"

# Weekend -> AI Error -> weekend fallback
def test_weekend_ai_failure_falls_back_to_hardcoded_string(client, auth_headers, db_session):
    saturday = real_date(2026, 7, 11)
    with patch(f"{MODULE}.date", new=_mock_date_for(saturday)), \
         patch(f"{MODULE}.generate_ai_quote", new_callable=AsyncMock,
               side_effect=openai.APIError("simulated failure", request=None, body=None)):
        response = client.get("/motivation", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["quote"] == "Remember to include yourself in the list of things you need to take care of today."

    log = db_session.query(MotivationLog).order_by(MotivationLog.id.desc()).first()
    assert log.source == "ai_weekend"
    assert log.trigger_context == "weekend"
    
# Exam today -> AI -> source=AI_EXAM, trigger_context="exam"
def test_exam_today_uses_ai_exam_quote(client, auth_headers, db_session):
    with patch(f"{MODULE}.date", new=_mock_date()), \
         patch(f"{MODULE}.get_has_exam_today", return_value=True), \
         patch(f"{MODULE}.generate_ai_quote", new_callable=AsyncMock, return_value="ai exam quote"):
        response = client.get("/motivation", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["quote"] == "ai exam quote"

    log = db_session.query(MotivationLog).order_by(MotivationLog.id.desc()).first()
    assert log.source == "ai_exam"
    assert log.trigger_context == "exam"
    
# Exam today -> AI Error -> exam fallback
def test_exam_ai_failure_falls_back_to_hardcoded_string(client, auth_headers, db_session):
    with patch(f"{MODULE}.date", new=_mock_date()), \
         patch(f"{MODULE}.get_has_exam_today", return_value=True), \
         patch(f"{MODULE}.generate_ai_quote", new_callable=AsyncMock,
               side_effect=openai.APIError("simulated failure", request=None, body=None)):
        response = client.get("/motivation", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["quote"] == "Good luck on your exam today!"

    log = db_session.query(MotivationLog).order_by(MotivationLog.id.desc()).first()
    assert log.source == "ai_exam"
    assert log.trigger_context == "exam"
    
# No hardest class today -> trigger_context="degree:fallback_no_class"
def test_no_hardest_class_forces_degree_branch(client, auth_headers, db_session):
    with patch(f"{MODULE}.date", new=_mock_date()), \
        patch(f"{MODULE}.get_has_exam_today", return_value=False), \
        patch(f"{MODULE}.get_hardest_class_today", return_value=None), \
        patch(f"{MODULE}.random.random", return_value=0.9), \
        patch(f"{MODULE}.get_static_degree_quote", return_value="static degree quote"):
            # We pick a random >= 0.5 (value that would've picked class branch )to prove the override 
        response = client.get("/motivation", headers=auth_headers)
            
    assert response.status_code == 200
    assert response.json()["quote"] == "static degree quote"
    
    log = db_session.query(MotivationLog).order_by(MotivationLog.id.desc()).first()
    assert log.trigger_context == "degree:fallback_no_class"

# hardest class + random -> trigger_context=f"class:{name}"
def test_class_available_random_selects_class_branch(client, auth_headers, db_session):
    with patch(f"{MODULE}.date", new=_mock_date()), \
        patch(f"{MODULE}.get_has_exam_today", return_value=False), \
        patch(f"{MODULE}.get_hardest_class_today", return_value="calculus 2"), \
        patch(f"{MODULE}.random.random", side_effect=[0.1, 0.1]), \
        patch(f"{MODULE}.generate_ai_quote", new_callable=AsyncMock, return_value="ai class quote"):
            # side effect: each successive call returns the next item in the list, in order
            response = client.get("/motivation", headers=auth_headers)
            
    assert response.status_code == 200
    assert response.json()["quote"] == "ai class quote"
    
    log = db_session.query(MotivationLog).order_by(MotivationLog.id.desc()).first()
    assert log.trigger_context == "class:calculus 2"
    assert log.source == "ai_class"

# hardest class but random to degree -> normal degree trigger context
def test_class_available_random_selects_degree_branch(client, auth_headers, db_session):
    with patch(f"{MODULE}.date", new=_mock_date()), \
         patch(f"{MODULE}.get_has_exam_today", return_value=False), \
         patch(f"{MODULE}.get_hardest_class_today", return_value="calculus 2"), \
         patch(f"{MODULE}.random.random", side_effect=[0.9, 0.9]), \
         patch(f"{MODULE}.get_static_degree_quote", return_value="static degree quote"):
        response = client.get("/motivation", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["quote"] == "static degree quote"

    log = db_session.query(MotivationLog).order_by(MotivationLog.id.desc()).first()
    assert log.trigger_context.startswith("degree:")
    assert log.trigger_context != "degree:fallback_no_class"

# Degree branch -> AI error -> source=static quote
def test_degree_branch_ai_failure_falls_back_to_static(client, auth_headers, db_session):
    with patch(f"{MODULE}.date", new=_mock_date()), \
         patch(f"{MODULE}.get_has_exam_today", return_value=False), \
         patch(f"{MODULE}.get_hardest_class_today", return_value=None), \
         patch(f"{MODULE}.random.random", side_effect=[0.1, 0.1]), \
         patch(f"{MODULE}.generate_ai_quote", new_callable=AsyncMock,
               side_effect=openai.APIError("simulated failure", request=None, body=None)), \
         patch(f"{MODULE}.get_static_degree_quote", return_value="fallback static quote"):
        response = client.get("/motivation", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["quote"] == "fallback static quote"

    log = db_session.query(MotivationLog).order_by(MotivationLog.id.desc()).first()
    assert log.source == "static_degree"
    
# Class branch -> all class_chance slices forced -> correct quote/source for each
def test_class_branch_all_four_slices(client, auth_headers, db_session):
    cases = [
        (0.1,  "ai class quote",                       "ai_class"),
        (0.55, "Good luck in today's classes!",         "static_class"),
        (0.75, "Good luck with calculus 2 today!",      "static_class"),
        (0.9,  "static class quote",                    "static_class"),
    ]

    for class_chance, expected_quote, expected_source in cases:
        with patch(f"{MODULE}.date", new=_mock_date()), \
             patch(f"{MODULE}.get_has_exam_today", return_value=False), \
             patch(f"{MODULE}.get_hardest_class_today", return_value="calculus 2"), \
             patch(f"{MODULE}.random.random", side_effect=[0.1, class_chance]), \
             patch(f"{MODULE}.generate_ai_quote", new_callable=AsyncMock, return_value="ai class quote"), \
             patch(f"{MODULE}.get_static_class_quote", return_value="static class quote"):
            response = client.get("/motivation", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["quote"] == expected_quote

        log = db_session.query(MotivationLog).order_by(MotivationLog.id.desc()).first()
        assert log.source == expected_source
        
# Class branch -> AI error -> source=static quote
def test_class_branch_ai_failure_falls_back_to_static(client, auth_headers, db_session):
    with patch(f"{MODULE}.date", new=_mock_date()), \
         patch(f"{MODULE}.get_has_exam_today", return_value=False), \
         patch(f"{MODULE}.get_hardest_class_today", return_value="calculus 2"), \
         patch(f"{MODULE}.random.random", side_effect=[0.1, 0.1]), \
         patch(f"{MODULE}.generate_ai_quote", new_callable=AsyncMock,
               side_effect=openai.APIError("simulated failure", request=None, body=None)), \
         patch(f"{MODULE}.get_static_class_quote", return_value="fallback static class quote"):
        response = client.get("/motivation", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["quote"] == "fallback static class quote"

    log = db_session.query(MotivationLog).order_by(MotivationLog.id.desc()).first()
    assert log.source == "static_class"
    assert log.trigger_context == "class:calculus 2"