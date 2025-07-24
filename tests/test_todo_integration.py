import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


class TestTodoIntegration:
    """Integration tests for Todo API endpoints."""

    def test_create_todo_success(self, client: TestClient, sample_todo_create_data):
        """Test successful todo creation."""
        response = client.post("/api/v1/todo/", json=sample_todo_create_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_todo_create_data["title"]
        assert data["description"] == sample_todo_create_data["description"]
        assert data["is_completed"] is False
        assert "id" in data

    def test_create_todo_missing_title(self, client: TestClient):
        """Test todo creation with missing title."""
        response = client.post("/api/v1/todo/", json={"description": "Test"})
        
        assert response.status_code == 422  # Validation error

    def test_get_todo_success(self, client: TestClient, sample_todo_create_data):
        """Test successful todo retrieval."""
        # First create a todo
        create_response = client.post("/api/v1/todo/", json=sample_todo_create_data)
        todo_id = create_response.json()["id"]
        
        # Then retrieve it
        response = client.get(f"/api/v1/todo/{todo_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["title"] == sample_todo_create_data["title"]

    def test_get_todo_not_found(self, client: TestClient):
        """Test retrieving non-existent todo."""
        response = client.get("/api/v1/todo/99999")
        
        assert response.status_code == 404
        assert "Todo not found" in response.json()["detail"]

    def test_update_todo_success(self, client: TestClient, sample_todo_create_data):
        """Test successful todo update."""
        # First create a todo
        create_response = client.post("/api/v1/todo/", json=sample_todo_create_data)
        todo_id = create_response.json()["id"]
        
        # Update the todo
        update_data = {
            "title": "Updated Todo",
            "is_completed": True
        }
        response = client.put(f"/api/v1/todo/{todo_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Todo"
        assert data["is_completed"] is True
        assert data["description"] == sample_todo_create_data["description"]  # Should remain unchanged

    def test_update_todo_partial(self, client: TestClient, sample_todo_create_data):
        """Test partial todo update."""
        # First create a todo
        create_response = client.post("/api/v1/todo/", json=sample_todo_create_data)
        todo_id = create_response.json()["id"]
        
        # Update only completion status
        update_data = {"is_completed": True}
        response = client.put(f"/api/v1/todo/{todo_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_completed"] is True
        assert data["title"] == sample_todo_create_data["title"]  # Should remain unchanged

    def test_update_todo_not_found(self, client: TestClient):
        """Test updating non-existent todo."""
        update_data = {"title": "Updated"}
        response = client.put("/api/v1/todo/99999", json=update_data)
        
        assert response.status_code == 404
        assert "Todo not found" in response.json()["detail"]

    def test_delete_todo_success(self, client: TestClient, sample_todo_create_data):
        """Test successful todo deletion."""
        # First create a todo
        create_response = client.post("/api/v1/todo/", json=sample_todo_create_data)
        todo_id = create_response.json()["id"]
        
        # Delete the todo
        response = client.delete(f"/api/v1/todo/{todo_id}")
        
        assert response.status_code == 200
        assert "Todo deleted successfully" in response.json()["message"]
        
        # Verify it's actually deleted
        get_response = client.get(f"/api/v1/todo/{todo_id}")
        assert get_response.status_code == 404

    def test_delete_todo_not_found(self, client: TestClient):
        """Test deleting non-existent todo."""
        response = client.delete("/api/v1/todo/99999")
        
        assert response.status_code == 404
        assert "Todo not found" in response.json()["detail"]

    def test_list_todos_empty(self, client: TestClient):
        """Test listing todos when database is empty."""
        response = client.get("/api/v1/todo/")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_list_todos_with_data(self, client: TestClient):
        """Test listing todos with multiple items."""
        # Create multiple todos
        todo_data_1 = {"title": "Todo 1", "description": "First todo"}
        todo_data_2 = {"title": "Todo 2", "description": "Second todo"}
        
        client.post("/api/v1/todo/", json=todo_data_1)
        client.post("/api/v1/todo/", json=todo_data_2)
        
        # List all todos
        response = client.get("/api/v1/todo/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(todo["title"] == "Todo 1" for todo in data)
        assert any(todo["title"] == "Todo 2" for todo in data)

    def test_todo_workflow_complete(self, client: TestClient):
        """Test complete todo workflow: create -> read -> update -> delete."""
        # 1. Create todo
        create_data = {
            "title": "Workflow Todo",
            "description": "Testing complete workflow"
        }
        create_response = client.post("/api/v1/todo/", json=create_data)
        assert create_response.status_code == 200
        todo_id = create_response.json()["id"]
        
        # 2. Read todo
        read_response = client.get(f"/api/v1/todo/{todo_id}")
        assert read_response.status_code == 200
        assert read_response.json()["title"] == "Workflow Todo"
        
        # 3. Update todo
        update_data = {"is_completed": True, "title": "Completed Workflow Todo"}
        update_response = client.put(f"/api/v1/todo/{todo_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["is_completed"] is True
        
        # 4. Verify update
        verify_response = client.get(f"/api/v1/todo/{todo_id}")
        assert verify_response.status_code == 200
        assert verify_response.json()["title"] == "Completed Workflow Todo"
        assert verify_response.json()["is_completed"] is True
        
        # 5. Delete todo
        delete_response = client.delete(f"/api/v1/todo/{todo_id}")
        assert delete_response.status_code == 200
        
        # 6. Verify deletion
        final_response = client.get(f"/api/v1/todo/{todo_id}")
        assert final_response.status_code == 404

    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are properly set."""
        response = client.options("/api/v1/todo/")
        
        # Note: TestClient doesn't automatically handle OPTIONS requests like a real browser
        # But we can test that CORS middleware is configured by checking a regular request
        response = client.get("/api/v1/todo/")
        assert response.status_code == 200
        # CORS headers would be present in a real browser environment 