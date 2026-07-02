def test_add_extracurricular_requires_authentication(client):
    response = client.post("/extracurriculars/add", json={"name": "Chess Club"})
    assert response.status_code == 401


def test_add_extracurricular_returns_correct_fields(client, auth_headers):
    response = client.post("/extracurriculars/add", json={
        "name": "Chess Club",
        "days": "TR",
        "location": "Room 101",
        "active_from": "2026-09-01",
        "active_until": "2026-12-15",
    }, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Chess Club"
    assert data["location"] == "Room 101"
    assert data["is_active"] is True

def test_list_extracurriculars_returns_only_active(client, auth_headers):
    client.post("/extracurriculars/add", json={"name": "Chess Club"}, headers=auth_headers)
    client.post("/extracurriculars/add", json={"name": "Soccer Team"}, headers=auth_headers)

    response = client.get("/extracurriculars/list", headers=auth_headers)
    assert response.status_code == 200
    names = [e["name"] for e in response.json()]
    assert "Chess Club" in names
    assert "Soccer Team" in names


def test_toggle_extracurricular_flips_active_status(client, auth_headers):
    add_response = client.post("/extracurriculars/add", json={
        "name": "Chess Club"
    }, headers=auth_headers)
    extra_id = add_response.json()["id"]

    # first toggle — should deactivate
    toggle_response = client.patch(
        f"/extracurriculars/toggle/{extra_id}",
        headers=auth_headers
    )
    assert toggle_response.status_code == 200
    assert toggle_response.json()["is_active"] is False

    # second toggle — should reactivate
    toggle_response = client.patch(
        f"/extracurriculars/toggle/{extra_id}",
        headers=auth_headers
    )
    assert toggle_response.json()["is_active"] is True


def test_toggle_nonexistent_extracurricular_returns_404(client, auth_headers):
    response = client.patch("/extracurriculars/toggle/9999", headers=auth_headers)
    assert response.status_code == 404