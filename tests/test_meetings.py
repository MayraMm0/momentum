def test_add_meeting_returns_correct_fields(client, auth_headers):
    response = client.post("/meetings/add", json={
        "title": "Study Group",
        "with_whom": "Alice, Bob",
        "days": "MW",
        "time_start": "14:00:00",
        "time_end": "15:30:00",
        "location": "Library",
        "recurrence_type": "weekly",
        "active_from": "2026-09-01",
        "active_until": "2026-12-15",
    }, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Study Group"
    assert data["with_whom"] == "Alice, Bob"
    assert data["recurrence_type"] == "weekly"


def test_add_meeting_requires_authentication(client):
    response = client.post("/meetings/add", json={"title": "Study Group"})
    assert response.status_code == 401


def test_list_meetings_returns_all_user_meetings(client, auth_headers):
    client.post("/meetings/add", json={"title": "Study Group"}, headers=auth_headers)
    client.post("/meetings/add", json={"title": "Advisor Check-in"}, headers=auth_headers)

    response = client.get("/meetings/list", headers=auth_headers)
    assert response.status_code == 200
    titles = [m["title"] for m in response.json()]
    assert "Study Group" in titles
    assert "Advisor Check-in" in titles


def test_update_meeting_changes_specified_fields(client, auth_headers):
    add_response = client.post("/meetings/add", json={
        "title": "Study Group",
        "location": "Library",
    }, headers=auth_headers)
    meeting_id = add_response.json()["id"]

    update_response = client.patch(f"/meetings/update/{meeting_id}", json={
        "title": "Study Group",
        "location": "Cafe",
    }, headers=auth_headers)

    assert update_response.status_code == 200
    assert update_response.json()["location"] == "Cafe"


def test_delete_meeting_removes_it_from_list(client, auth_headers):
    add_response = client.post("/meetings/add", json={
        "title": "Study Group"
    }, headers=auth_headers)
    meeting_id = add_response.json()["id"]

    delete_response = client.delete(
        f"/meetings/delete/{meeting_id}",
        headers=auth_headers
    )
    assert delete_response.status_code == 200

    list_response = client.get("/meetings/list", headers=auth_headers)
    titles = [m["title"] for m in list_response.json()]
    assert "Study Group" not in titles


def test_delete_nonexistent_meeting_returns_404(client, auth_headers):
    response = client.delete("/meetings/delete/9999", headers=auth_headers)
    assert response.status_code == 404