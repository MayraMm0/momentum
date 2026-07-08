from datetime import date, datetime, timedelta

# Auth guard
def test_schedule_endpoint_requires_authentication(client):
    response = client.get("/schedule/week")
    
    assert response.status_code == 401
    
# Response has correct structure
def test_schedule_week_returns_correct_structure(client, auth_headers):
    response = client.get("/schedule/week", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "week_start" in data
    assert "week_end" in data
    assert "days" in data
    assert len(data["days"]) == 7
    assert "tasks" in data
    
# Sunday - Saturday structure (needs correction)
def test_week_start_is_Sunday_and_week_end_is_Saturday(client, auth_headers):
    response = client.get("/schedule/week", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    
    week_start = date.fromisoformat(data["week_start"])
    week_end = date.fromisoformat(data["week_end"])
    
    assert week_start.weekday() == 6
    assert (week_end - week_start).days == 6
    
# A couse scheduled everyday appears in all 7 days
def test_daily_course_appears_all_7_days(client, auth_headers):
    course_response = client.post("/courses/add", json={
        "name": "Daily Lecture",
        "days": "MTWRFSU",
    }, headers=auth_headers)
    assert course_response.status_code == 200

    response = client.get("/schedule/week", headers=auth_headers)
    assert response.status_code == 200
    courses = [d["courses"] for d in response.json()["days"]]
    course_count = 0
    for course in courses:
        if not course: continue
        if course[0]["name"] == "Daily Lecture": course_count+=1
    assert course_count == 7
    
# A course scheduled for only one specific day appears in exactly one DaySchedule entry
def test_one_day_course_appears_on_one_day(client, auth_headers):
    course_response = client.post("/courses/add", json={
        "name": "Daily Lecture",
        "days": "M",
    }, headers=auth_headers)
    assert course_response.status_code == 200

    response = client.get("/schedule/week", headers=auth_headers)
    assert response.status_code == 200
    courses = [d["courses"] for d in response.json()["days"]]
    course_count = 0
    for course in courses:
        if not course: continue
        if course[0]["name"] == "Daily Lecture": course_count+=1
    assert course_count == 1
    
# Inactive course is excluded from schedule
def test_inactive_course_is_excluded_from_schedule(client, auth_headers):
    add_response = client.post("/courses/add", json={
        "name": "Thermodynamics",
        "days": "MTWRFSU"
    }, headers=auth_headers)
    course_id = add_response.json()["id"]

    deactivate_response = client.patch(
        f"/courses/deactivate/{course_id}",
        headers=auth_headers
    )
    assert deactivate_response.status_code == 200

    response = client.get("/schedule/week", headers=auth_headers)
    assert response.status_code == 200
    courses = [d["courses"] for d in response.json()["days"]]
    for course in courses:
        assert not course

# Extracurricular respects active_from/active_until across the week
def test_extracurricular_respects_active_from_mid_week(client, auth_headers):
    today = date.today()
    days_since_sunday = (today.weekday() + 1) % 7
    week_start = today - timedelta(days=days_since_sunday)
    mid_week_start = week_start + timedelta(days=3)  # Wednesday of this week
    week_end = week_start + timedelta(days=6)

    add_response = client.post("/extracurriculars/add", json={
        "name": "Chess Club",
        "days": "MTWRFSU",
        "active_from": mid_week_start.isoformat(),
        "active_until": week_end.isoformat(),
    }, headers=auth_headers)
    assert add_response.status_code == 200

    response = client.get("/schedule/week", headers=auth_headers)
    assert response.status_code == 200
    days_data = response.json()["days"]

    for i, day in enumerate(days_data):
        names = [e["name"] for e in day["extracurriculars"]]
        if i < 3:
            assert "Chess Club" not in names
        else:
            assert "Chess Club" in names

# A task with date_finish inside this week appears in the flat tasks list
def test_task_with_date_finish_inside_week_is_included(client, auth_headers):
    today = date.today()
    task_response = client.post("/tasks/add", json={
        "title": "Problem set 1 diff eqs",
        "date_finish": datetime.combine(today, datetime.min.time()).isoformat(),
    }, headers=auth_headers)
    assert task_response.status_code == 200

    response = client.get("/schedule/week", headers=auth_headers)
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()["tasks"]]
    assert "Problem set 1 diff eqs" in titles

# A task with date_finish outside this week is excluded
def test_task_with_date_finish_outside_week_is_excluded(client, auth_headers):
    task_response = client.post("/tasks/add", json={
        "title": "Problem set 1 diff eqs",
        "date_finish": datetime(2100, 5, 17).isoformat()
    }, headers=auth_headers)
    assert task_response.status_code == 200
    
    response = client.get("/schedule/week", headers=auth_headers)
    assert response.status_code == 200
    assert not response.json()["tasks"]
    

# A task with no date_finish at all is included
def test_task_with_no_date_finish_is_excluded(client, auth_headers):
    task_response = client.post("/tasks/add", json={
        "title": "Problem set 1 diff eqs",
    }, headers=auth_headers)
    assert task_response.status_code == 200
    
    response = client.get("/schedule/week", headers=auth_headers)
    assert response.status_code == 200
    tasks_titles = [t["title"] for t in response.json()["tasks"]]
    
    assert "Problem set 1 diff eqs" in tasks_titles
    
# A completed task is excluded even if its date_finish is this week
def test_completed_task_excluded_from_weekly_tasks(client, auth_headers):
    today = date.today()
    task_response = client.post("/tasks/add", json={
        "title": "Problem set 1 diff eqs",
        "date_finish": datetime.combine(today, datetime.min.time()).isoformat(),
    }, headers=auth_headers)
    assert task_response.status_code == 200
    task_id = task_response.json()["id"]

    complete_response = client.patch(f"/tasks/complete/{task_id}", headers=auth_headers)
    assert complete_response.status_code == 200

    response = client.get("/schedule/week", headers=auth_headers)
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()["tasks"]]
    assert "Problem set 1 diff eqs" not in titles

# A task due at a specific time late on the last day of the week (Saturday evening) is still included
def test_task_due_saturday_evening_is_included(client, auth_headers):
    today = date.today()
    days_since_sunday = (today.weekday() + 1) % 7
    week_start = today - timedelta(days=days_since_sunday)
    saturday = week_start + timedelta(days=6)
    saturday_evening = datetime.combine(saturday, datetime.min.time()) + timedelta(hours=23, minutes=30)

    task_response = client.post("/tasks/add", json={
        "title": "Late Saturday Task",
        "date_finish": saturday_evening.isoformat(),
    }, headers=auth_headers)
    assert task_response.status_code == 200

    response = client.get("/schedule/week", headers=auth_headers)
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()["tasks"]]
    assert "Late Saturday Task" in titles