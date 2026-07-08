from backend.models import NlpPrediction

# Auth for adding a task
def test_add_task_requires_authentication(client):
    response = client.post("/tasks/add", json={
        "title": "Problem set 1 diff eqs",
    })
    
    assert response.status_code == 401
    
# Create returns correct fields
def test_add_task_returns_task_with_correct_fields(client, auth_headers):
    response = client.post("/tasks/add", json={
        "title": "Problem set 1 diff eqs",
        "description": "10 problems integrating factor"
    }, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Problem set 1 diff eqs"
    assert data["description"] == "10 problems integrating factor"
    assert data["has_deadline"] == True
    assert "user_id" in data
    

# Classifier fills type/subtype when client omits both
def test_add_task_classifier_fills_type_subtype(client, auth_headers):
    response = client.post("/tasks/add", json={
        "title": "Study for diff eqs exam",
        "description": "final exam"
    }, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Study for diff eqs exam"
    assert data["type"] == "academic"
    assert data["subtype"] == "exam"
    
# Client-provided type/subtype override the classifier 
def test_add_task_client_overrides_classifier(client, auth_headers):
    response = client.post("/tasks/add", json={
        "title": "Study for diff eqs exam",
        "description": "final exam",
        "type": "personal"
    }, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Study for diff eqs exam"
    assert data["type"] == "personal"
    
# No keyword match falls back to academic
def test_add_task_classifier_fallback_to_academic(client, auth_headers):
    response = client.post("/tasks/add", json={
        "title": "check canvas for diff eqs",
        "description": "check grades",
    }, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "check canvas for diff eqs"
    assert data["type"] == "academic"
    assert data["subtype"] == None
    
# NlpPrediction row gets created
def test_add_task_creates_nlp_prediction_row(client, auth_headers, db_session):
    response = client.post("/tasks/add", json={
        "title": "Study for diff eqs exam",
        "description": "final exam"
    }, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    task_id = data["id"]
    
    prediction = db_session.query(NlpPrediction).filter(NlpPrediction.task_id == task_id).first()
    assert prediction is not None
    assert prediction.predicted_type == "academic"
    assert prediction.predicted_subtype == "exam"
    
# user overrode is True when client disagrees with classifier
def test_add_task_user_overrode_flag(client, auth_headers, db_session):
    response = client.post("/tasks/add", json={
        "title": "Study for diff eqs exam",
        "description": "final exam",
        "type": "personal"
    }, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    task_id = data["id"]
    
    prediction = db_session.query(NlpPrediction).filter(NlpPrediction.task_id == task_id).first()
    assert prediction is not None
    assert prediction.user_overrode_type == True

# user overrode is False when client matches classifier
def test_add_task_user_overrode_flag_false(client, auth_headers, db_session):
    response = client.post("/tasks/add", json={
        "title": "Study for diff eqs exam",
        "description": "final exam",
        "type": "academic"
    }, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    task_id = data["id"]
    
    prediction = db_session.query(NlpPrediction).filter(NlpPrediction.task_id == task_id).first()
    assert prediction is not None
    assert prediction.user_overrode_type == False
    
# Auth for getting the list of tasks
def test_list_tasks_requires_authentication(client):
    response = client.get("/tasks/list")
    
    assert response.status_code == 401
    
# List returns incompleted tasks
def test_list_tasks_returns_created_tasks(client, auth_headers):
    task1 = client.post("/tasks/add", json={
        "title": "Task 1",
    }, headers=auth_headers)
    task2 = client.post("/tasks/add", json={
        "title": "Task 2",
    }, headers=auth_headers)
    
    response = client.get("/tasks/list", headers=auth_headers)
    assert response.status_code == 200
    titles = [c["title"] for c in response.json()]
    assert "Task 1" in titles
    assert "Task 2" in titles
    
# List excludes incompleted tasks
def test_list_tasks_excludes_completed_tasks(client, auth_headers):
    task1 = client.post("/tasks/add", json={
        "title": "Task 1",
    }, headers=auth_headers)
    task2 = client.post("/tasks/add", json={
        "title": "Task 2",
    }, headers=auth_headers)
    
    # Complete task 1
    task1_id = task1.json()["id"]
    client.patch(f"/tasks/complete/{task1_id}", headers=auth_headers)
    
    response = client.get("/tasks/list", headers=auth_headers)
    assert response.status_code == 200
    titles = [c["title"] for c in response.json()]
    assert "Task 1" not in titles
    assert "Task 2" in titles
    
# Plain list does not include nlp_prediction field
def test_list_tasks_plain_does_not_include_nlp_prediction(client, auth_headers):
    task1 = client.post("/tasks/add", json={
        "title": "Task 1",
    }, headers=auth_headers)
    
    response = client.get("/tasks/list", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()[0]
    assert "nlp_prediction" not in data
    
# List with predictions requires auth
def test_lists_tasks_with_predictions_requires_authentication(client):
    response = client.get("/tasks/list/with-predictions")
    
    assert response.status_code == 401

# List with predictions returns nlp_prediction field
def test_list_tasks_with_predictions_includes_nlp_prediction(client, auth_headers):
    task1 = client.post("/tasks/add", json={
        "title": "Task 1",
    }, headers=auth_headers)
    
    response = client.get("/tasks/list/with-predictions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()[0]
    assert "nlp_prediction" in data

# List with predictions excludes completed tasks
def test_list_tasks_with_predictions_excludes_completed_tasks(client, auth_headers):
    task1 = client.post("/tasks/add", json={
        "title": "Task 1",
    }, headers=auth_headers)
    task2 = client.post("/tasks/add", json={
        "title": "Task 2",
    }, headers=auth_headers)
    
    # Complete task 1
    task1_id = task1.json()["id"]
    client.patch(f"/tasks/complete/{task1_id}", headers=auth_headers)
    
    response = client.get("/tasks/list/with-predictions", headers=auth_headers)
    assert response.status_code == 200
    titles = [c["title"] for c in response.json()]
    assert "Task 1" not in titles
    assert "Task 2" in titles

# Update task endpoint requires auth
def test_update_task_requires_authentication(client):
    response = client.patch("/tasks/update/1", json={
        "title": "Updated Task"
    })
    
    assert response.status_code == 401

# Update task endpoint changes only specified fields
def test_update_task_changes_only_specified_fields(client, auth_headers):
    add_response = client.post("/tasks/add", json={
        "title": "Task 1",
        "description": "Initial description"
    }, headers=auth_headers)
    task_id = add_response.json()["id"]

    update_response = client.patch(f"/tasks/update/{task_id}", json={
        "title": "Updated Task 1"
    }, headers=auth_headers)

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["title"] == "Updated Task 1"
    assert data["description"] == "Initial description"

# update on nonexistent task shows 404
def test_update_nonexistent_task_shows_404(client, auth_headers):
    update_response = client.patch(f"/tasks/update/9999", json={
        "title": "Updated Task"
    }, headers=auth_headers)

    assert update_response.status_code == 404

# Updating type post-creation sets user_overrode_type = True
def test_update_task_type_sets_user_overrode_flag(client, auth_headers, db_session):
    add_response = client.post("/tasks/add", json={
        "title": "Task 1",
        "description": "Initial description"
    }, headers=auth_headers)
    task_id = add_response.json()["id"]

    update_response = client.patch(f"/tasks/update/{task_id}", json={
        "type": "personal"
    }, headers=auth_headers)

    assert update_response.status_code == 200

    prediction = db_session.query(NlpPrediction).filter(NlpPrediction.task_id == task_id).first()
    assert prediction is not None
    assert prediction.user_overrode_type == True
    
# Updating a field unrelated to type/subtype (e.g. location) does NOT touch user_overrode_type
def test_update_task_unrelated_field_does_not_change_user_overrode_flag(client, auth_headers, db_session):
    add_response = client.post("/tasks/add", json={
        "title": "Task 1",
        "description": "Initial description"
    }, headers=auth_headers)
    task_id = add_response.json()["id"]

    update_response = client.patch(f"/tasks/update/{task_id}", json={
        "location": "Library"
    }, headers=auth_headers)

    assert update_response.status_code == 200

    prediction = db_session.query(NlpPrediction).filter(NlpPrediction.task_id == task_id).first()
    assert prediction is not None
    assert prediction.user_overrode_type == False

# Complete task requires auth
def test_complete_task_requires_authentication(client):
    response = client.patch("/tasks/complete/1")
    
    assert response.status_code == 401
    
# Toggle on a non existent task shows 404
def test_toggle_nonexistent_task_shows_404(client, auth_headers):
    response = client.patch("/tasks/complete/9999", headers=auth_headers)
    
    assert response.status_code == 404
    
# Toggle completed from false to true and back
def test_toggle_task_completion_and_back(client, auth_headers):
    add_response = client.post("/tasks/add", json={
        "title": "Task 1",
    }, headers=auth_headers)
    task_id = add_response.json()["id"]

    # Toggle to completed
    complete_response = client.patch(f"/tasks/complete/{task_id}", headers=auth_headers)
    assert complete_response.status_code == 200
    assert complete_response.json()["completed"] == True

    # Toggle back to not completed
    incomplete_response = client.patch(f"/tasks/complete/{task_id}", headers=auth_headers)
    assert incomplete_response.status_code == 200
    assert incomplete_response.json()["completed"] == False
    
# delete task requiered auth
def test_delete_task_requires_authentication(client):
    response = client.delete("/tasks/delete/1")
    
    assert response.status_code == 401

# delete nonexistent task shows 404
def test_delete_nonexistent_task_shows_404(client, auth_headers):
    response = client.delete("/tasks/delete/9999", headers=auth_headers)
    
    assert response.status_code == 404
    
# delete task removes it from list
def test_delete_task_removes_it_from_list(client, auth_headers):
    add_response = client.post("/tasks/add", json={
        "title": "Task 1",
    }, headers=auth_headers)
    task_id = add_response.json()["id"]

    delete_response = client.delete(f"/tasks/delete/{task_id}", headers=auth_headers)
    assert delete_response.status_code == 200

    list_response = client.get("/tasks/list", headers=auth_headers)
    titles = [c["title"] for c in list_response.json()]
    assert "Task 1" not in titles
    