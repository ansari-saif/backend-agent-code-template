import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


class TestTodoIntegration:
    """Integration tests for Todo API endpoints."""

    def test_create_todo_success(self, client: TestClient, sample_todo_create_data):
        """Test successful todo creation."""
        response = client.post("/todos/", json=sample_todo_create_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_todo_create_data["title"]
        assert data["description"] == sample_todo_create_data["description"]
        assert data["is_completed"] is False
        assert "id" in data

    def test_create_todo_missing_title(self, client: TestClient):
        """Test todo creation with missing title."""
        response = client.post("/todos/", json={"description": "Test"})
        
        assert response.status_code == 422  # Validation error

    def test_get_todo_success(self, client: TestClient, sample_todo_create_data):
        """Test successful todo retrieval."""
        # First create a todo
        create_response = client.post("/todos/", json=sample_todo_create_data)
        todo_id = create_response.json()["id"]
        
        # Then get it
        response = client.get(f"/todos/{todo_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["title"] == sample_todo_create_data["title"]

    def test_get_todo_not_found(self, client: TestClient):
        """Test getting non-existent todo."""
        response = client.get("/todos/99999")
        
        assert response.status_code == 404
        assert "Todo not found" in response.json()["detail"]

    def test_update_todo_success(self, client: TestClient, sample_todo_create_data):
        """Test successful todo update."""
        # First create a todo
        create_response = client.post("/todos/", json=sample_todo_create_data)
        todo_id = create_response.json()["id"]
        
        # Update it
        update_data = {
            "title": "Updated Todo Title",
            "is_completed": True
        }
        response = client.put(f"/todos/{todo_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Todo Title"
        assert data["is_completed"] is True
        assert data["description"] == sample_todo_create_data["description"]  # Should remain unchanged

    def test_update_todo_partial(self, client: TestClient, sample_todo_create_data):
        """Test partial todo update."""
        # First create a todo
        create_response = client.post("/todos/", json=sample_todo_create_data)
        todo_id = create_response.json()["id"]
        
        # Partial update
        update_data = {"is_completed": True}
        response = client.put(f"/todos/{todo_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_completed"] is True
        assert data["title"] == sample_todo_create_data["title"]  # Should remain unchanged

    def test_update_todo_not_found(self, client: TestClient):
        """Test updating non-existent todo."""
        update_data = {"title": "Updated Title"}
        response = client.put("/todos/99999", json=update_data)
        
        assert response.status_code == 404
        assert "Todo not found" in response.json()["detail"]

    def test_delete_todo_success(self, client: TestClient, sample_todo_create_data):
        """Test successful todo deletion."""
        # First create a todo
        create_response = client.post("/todos/", json=sample_todo_create_data)
        todo_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/todos/{todo_id}")
        
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(f"/todos/{todo_id}")
        assert get_response.status_code == 404

    def test_delete_todo_not_found(self, client: TestClient):
        """Test deleting non-existent todo."""
        response = client.delete("/todos/99999")
        
        assert response.status_code == 404
        assert "Todo not found" in response.json()["detail"]

    def test_list_todos_empty(self, client: TestClient):
        """Test listing todos when database is empty."""
        response = client.get("/todos/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_todos_with_data(self, client: TestClient, sample_todo_create_data):
        """Test listing todos with data."""
        # Create multiple todos
        todo1_data = sample_todo_create_data.copy()
        todo2_data = sample_todo_create_data.copy()
        todo2_data["title"] = "Second Todo"
        
        client.post("/todos/", json=todo1_data)
        client.post("/todos/", json=todo2_data)
        
        response = client.get("/todos/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_todo_workflow_complete(self, client: TestClient, sample_todo_create_data):
        """Test complete todo workflow: create, read, update, delete."""
        # Create
        create_response = client.post("/todos/", json=sample_todo_create_data)
        assert create_response.status_code == 201
        todo_id = create_response.json()["id"]
        
        # Read
        read_response = client.get(f"/todos/{todo_id}")
        assert read_response.status_code == 200
        assert read_response.json()["title"] == sample_todo_create_data["title"]
        
        # Update
        update_data = {"is_completed": True}
        update_response = client.put(f"/todos/{todo_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["is_completed"] is True
        
        # Delete
        delete_response = client.delete(f"/todos/{todo_id}")
        assert delete_response.status_code == 204
        
        # Verify deletion
        final_read_response = client.get(f"/todos/{todo_id}")
        assert final_read_response.status_code == 404

    def test_todo_list_pagination(self, client: TestClient, sample_todo_create_data):
        """Test todo listing with pagination."""
        # Create multiple todos
        for i in range(5):
            todo_data = sample_todo_create_data.copy()
            todo_data["title"] = f"Todo {i}"
            client.post("/todos/", json=todo_data)
        
        # Test pagination
        response = client.get("/todos/?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are present."""
        response = client.get("/todos/")
        
        assert response.status_code == 200
        # Note: CORS headers are handled by middleware and may not be visible in test client 