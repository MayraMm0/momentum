# Proves route is protected
def test_add_course_requires_authentication(client):
    response = client.post("/courses/add", json={
        "name": "Thermodynamics",
    })
    
    assert response.status_code == 401
    
def test_add_course_returns_course_with_correct_fields(client, auth_headers):
    response = client.post("/courses/add", json={
        "name": "Thermodynamics",
        "professor": "Dr. Smith",
        "days": "MWF",
        "semester": "Fall 2026",
        "difficulty_rank": 3,
        "color_hex": "#FF5733"
    }, headers=auth_headers)
    
    print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Thermodynamics"
    assert data["professor"] == "Dr. Smith"
    assert data["difficulty_rank"] == 3
    assert data["is_active"] is True
    assert "user_id" in data
    
def test_list_courses_returns_only_active_courses(client, auth_headers):
    client.post("/courses/add", json={"name": "Thermodynamics"}, headers=auth_headers)
    client.post("/courses/add", json={"name": "Calculus"}, headers=auth_headers)
    
    response = client.get("/courses/list", headers=auth_headers)
    assert response.status_code == 200
    names = [c["name"] for c in response.json()]
    assert "Thermodynamics" in names
    assert "Calculus" in names
    
def test_update_course_changes_only_specified_fields(client, auth_headers):
    add_response = client.post("/courses/add", json={
        "name": "Thermodynamics",
        "professor": "Dr. Smith",
        "difficulty_rank": 2,
    }, headers=auth_headers)
    course_id = add_response.json()["id"]

    update_response = client.patch(f"/courses/update/{course_id}", json={
        "name": "Applied Thermodynamics",
        "difficulty_rank": 2,
    }, headers=auth_headers)

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Applied Thermodynamics"
    assert data["professor"] == "Dr. Smith"
    assert data["difficulty_rank"] == 2

def test_deactivate_course_removes_it_from_list(client, auth_headers):
    add_response = client.post("/courses/add", json={
        "name": "Thermodynamics"
    }, headers=auth_headers)
    course_id = add_response.json()["id"]

    deactivate_response = client.patch(
        f"/courses/deactivate/{course_id}",
        headers=auth_headers
    )
    assert deactivate_response.status_code == 200

    list_response = client.get("/courses/list", headers=auth_headers)
    names = [c["name"] for c in list_response.json()]
    assert "Thermodynamics" not in names
    
def test_deactivate_nonexistent_course_returns_404(client, auth_headers):
    response = client.patch("/courses/deactivate/9999", headers=auth_headers)
    assert response.status_code == 404