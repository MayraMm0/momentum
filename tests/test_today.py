def test_today_returns_correct_structure(client, auth_headers):
    response = client.get("/today", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "date" in data
    assert "courses" in data
    assert "extracurriculars" in data
    assert "meetings" in data


def test_today_requires_authentication(client):
    response = client.get("/today")
    assert response.status_code == 401


def test_today_includes_course_scheduled_for_every_day(client, auth_headers):
    # "MTWRFSU" covers all days, so this course always appears in /today
    client.post("/courses/add", json={
        "name": "Daily Lecture",
        "days": "MTWRFSU",
    }, headers=auth_headers)

    response = client.get("/today", headers=auth_headers)
    assert response.status_code == 200
    names = [c["name"] for c in response.json()["courses"]]
    assert "Daily Lecture" in names


def test_today_excludes_course_not_scheduled_today(client, auth_headers):
    from datetime import date
    # figure out a day code that is NOT today
    day_codes = {0: "M", 1: "T", 2: "W", 3: "R", 4: "F", 5: "S", 6: "U"}
    today_code = day_codes[date.today().weekday()]
    other_code = next(v for v in day_codes.values() if v != today_code)

    client.post("/courses/add", json={
        "name": "Other Day Course",
        "days": other_code,
    }, headers=auth_headers)

    response = client.get("/today", headers=auth_headers)
    names = [c["name"] for c in response.json()["courses"]]
    assert "Other Day Course" not in names


def test_today_excludes_inactive_course(client, auth_headers):
    add_response = client.post("/courses/add", json={
        "name": "Daily Lecture",
        "days": "MTWRFSU",
    }, headers=auth_headers)
    course_id = add_response.json()["id"]

    client.patch(f"/courses/deactivate/{course_id}", headers=auth_headers)

    response = client.get("/today", headers=auth_headers)
    names = [c["name"] for c in response.json()["courses"]]
    assert "Daily Lecture" not in names