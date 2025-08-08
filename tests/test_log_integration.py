import pytest


@pytest.mark.integration
def test_create_and_get_log(client):
    # Create
    create_resp = client.post("/log/", json={"title": "First log"})
    assert create_resp.status_code == 201, create_resp.text
    data = create_resp.json()
    assert data["title"] == "First log"
    assert "log_id" in data
    assert "created_at" in data

    # Get
    log_id = data["log_id"]
    get_resp = client.get(f"/log/{log_id}")
    assert get_resp.status_code == 200
    got = get_resp.json()
    assert got["log_id"] == log_id
    assert got["title"] == "First log"

    # List
    list_resp = client.get("/log/")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert isinstance(items, list)
    assert any(item["log_id"] == log_id for item in items)


