# Auth guard
def test_add_project_requires_authentication(client):
    response = client.post("/projects/add", json={
        "title": "Diff Eqs Project",
    })
    
    assert response.status_code == 401
    
# Create returns correct fields, including status=="active"
def test_add_project_returns_project_with_correct_fields(client, auth_headers):
    response = client.post("/projects/add", json={
        "title": "Diff Eqs Project",
        "priority": 3
    }, headers=auth_headers)
    
    print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Diff Eqs Project"
    assert data["priority"] == 3
    assert data["status"] == "active"
    assert "user_id" in data
    
# List only returns active projects
def test_list_projects_returns_only_active_projects(client, auth_headers):
    client.post("/projects/add", json={"title": "Project1"}, headers=auth_headers)
    client.post("/projects/add", json={"title": "Project2"}, headers=auth_headers)
    
    response = client.get("/projects/list", headers=auth_headers)
    assert response.status_code == 200
    titles = [c["title"] for c in response.json()]
    assert "Project1" in titles
    assert "Project2" in titles
    
# Update changes only specified fields
def test_update_project_changes_only_specified_fields(client, auth_headers):
    add_response = client.post("/projects/add", json={
        "title": "Project 1",
    }, headers=auth_headers)
    project_id = add_response.json()["id"]

    update_response = client.patch(f"/projects/update/{project_id}", json={
        "title": "Project 1",
        "priority": 3,
    }, headers=auth_headers)

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["title"] == "Project 1"
    assert data["priority"] == 3
    
# Complete endpoint sets status to "completed"
def test_complete_project_sets_status_as_completed(client, auth_headers):
    add_response = client.post("/projects/add", json={
        "title": "Project1"
    }, headers=auth_headers)
    project_id = add_response.json()["id"]
    
    completed_response = client.patch(
        f"/projects/complete/{project_id}",
        headers=auth_headers
    )
    assert completed_response.status_code == 200
    
    assert completed_response.json()["status"] == "completed"

# Test list doesnt show a completed project
def test_complete_project_removes_it_from_list(client, auth_headers):
    add_response = client.post("/projects/add", json={
        "title": "Project1"
    }, headers=auth_headers)
    project_id = add_response.json()["id"]

    completed_response = client.patch(
        f"/projects/complete/{project_id}",
        headers=auth_headers
    )
    assert completed_response.status_code == 200

    list_response = client.get("/projects/list", headers=auth_headers)
    titles = [c["title"] for c in list_response.json()]
    assert "Project1" not in titles
    
# Archive endpoint sets status to "archived"
def test_archive_project_sets_status_as_archived(client, auth_headers):
    add_response = client.post("/projects/add", json={
        "title": "Project1"
    }, headers=auth_headers)
    project_id = add_response.json()["id"]
    
    archive_response = client.patch(
        f"/projects/archive/{project_id}",
        headers=auth_headers
    )
    assert archive_response.status_code == 200
    assert archive_response.json()["status"] == "archived"

# Test list doesnt show an archived project
def test_archive_project_removes_it_from_list(client, auth_headers):
    add_response = client.post("/projects/add", json={
        "title": "Project1"
    }, headers=auth_headers)
    project_id = add_response.json()["id"]

    archive_response = client.patch(
        f"/projects/archive/{project_id}",
        headers=auth_headers
    )
    assert archive_response.status_code == 200

    list_response = client.get("/projects/list", headers=auth_headers)
    titles = [c["title"] for c in list_response.json()]
    assert "Project1" not in titles

# 404 on completing/archiving/updating a non-existent project
def test_archive_nonexistent_project_returns_404(client, auth_headers):
    response = client.patch("/projects/archive/9999", headers=auth_headers)
    assert response.status_code == 404
    
def test_complete_nonexistent_project_returns_404(client, auth_headers):
    response = client.patch("/projects/complete/9999", headers=auth_headers)
    assert response.status_code == 404
    
def test_update_nonexistent_project_returns_404(client, auth_headers):
    response = client.patch("/projects/update/9999", json={
        "title": "Project 1",
        "priority": 3,
    }, headers=auth_headers)
    assert response.status_code == 404