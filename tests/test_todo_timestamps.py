import pytest
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.models.todo import Todo, TodoCreate


class TestTodoTimestamps:
    """Test cases for created_at and updated_at timestamp functionality."""

    def test_todo_creation_sets_timestamps(self, session: Session):
        """Test that creating a todo sets both created_at and updated_at timestamps."""
        before_creation = datetime.now()
        
        todo_data = TodoCreate(title="Test Todo", description="Test description")
        todo = Todo.from_orm(todo_data)
        session.add(todo)
        session.commit()
        session.refresh(todo)
        
        after_creation = datetime.now()
        
        assert todo.created_at is not None
        assert todo.updated_at is not None
        assert before_creation <= todo.created_at <= after_creation
        assert before_creation <= todo.updated_at <= after_creation
        # Both timestamps should be very close at creation
        assert abs((todo.created_at - todo.updated_at).total_seconds()) < 1

    def test_todo_creation_via_api_includes_timestamps(self, client: TestClient):
        """Test that API creation includes timestamps in response."""
        todo_data = {
            "title": "API Test Todo",
            "description": "Test via API"
        }
        
        response = client.post("/api/v1/todo/", json=todo_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "created_at" in data
        assert "updated_at" in data
        assert data["created_at"] is not None
        assert data["updated_at"] is not None
        
        # Verify timestamps are valid datetime strings
        created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        updated_at = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
        
        assert isinstance(created_at, datetime)
        assert isinstance(updated_at, datetime)

    def test_todo_update_changes_updated_at(self, client: TestClient):
        """Test that updating a todo changes the updated_at timestamp but not created_at."""
        # Create a todo
        create_data = {
            "title": "Original Title",
            "description": "Original description"
        }
        create_response = client.post("/api/v1/todo/", json=create_data)
        todo_id = create_response.json()["id"]
        original_created_at = create_response.json()["created_at"]
        original_updated_at = create_response.json()["updated_at"]
        
        # Wait a small amount to ensure timestamp difference
        time.sleep(0.1)
        
        # Update the todo
        update_data = {"title": "Updated Title"}
        update_response = client.put(f"/api/v1/todo/{todo_id}", json=update_data)
        
        assert update_response.status_code == 200
        updated_data = update_response.json()
        
        # created_at should remain unchanged
        assert updated_data["created_at"] == original_created_at
        
        # updated_at should be different (newer)
        assert updated_data["updated_at"] != original_updated_at
        
        new_updated_at = datetime.fromisoformat(updated_data["updated_at"].replace('Z', '+00:00'))
        orig_updated_at = datetime.fromisoformat(original_updated_at.replace('Z', '+00:00'))
        
        assert new_updated_at > orig_updated_at

    def test_todo_partial_update_changes_updated_at(self, client: TestClient):
        """Test that partial updates also change the updated_at timestamp."""
        # Create a todo
        create_data = {
            "title": "Test Todo",
            "description": "Test description",
            "is_completed": False
        }
        create_response = client.post("/api/v1/todo/", json=create_data)
        todo_id = create_response.json()["id"]
        original_updated_at = create_response.json()["updated_at"]
        
        # Wait a small amount to ensure timestamp difference
        time.sleep(0.1)
        
        # Update only the completion status
        update_data = {"is_completed": True}
        update_response = client.put(f"/api/v1/todo/{todo_id}", json=update_data)
        
        assert update_response.status_code == 200
        updated_data = update_response.json()
        
        # updated_at should be different
        assert updated_data["updated_at"] != original_updated_at
        assert updated_data["is_completed"] is True
        # Other fields should remain unchanged
        assert updated_data["title"] == create_data["title"]
        assert updated_data["description"] == create_data["description"]

    def test_todo_get_includes_timestamps(self, client: TestClient):
        """Test that retrieving a todo includes timestamp fields."""
        # Create a todo
        create_data = {"title": "Get Test Todo", "description": "Test retrieval"}
        create_response = client.post("/api/v1/todo/", json=create_data)
        todo_id = create_response.json()["id"]
        
        # Retrieve the todo
        get_response = client.get(f"/api/v1/todo/{todo_id}")
        
        assert get_response.status_code == 200
        data = get_response.json()
        
        assert "created_at" in data
        assert "updated_at" in data
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

    def test_todo_list_includes_timestamps(self, client: TestClient):
        """Test that listing todos includes timestamp fields for all items."""
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
        
        for todo in data:
            assert "created_at" in todo
            assert "updated_at" in todo
            assert todo["created_at"] is not None
            assert todo["updated_at"] is not None

    def test_timestamps_are_immutable_on_creation(self, session: Session):
        """Test that created_at timestamp cannot be modified after creation."""
        todo_data = TodoCreate(title="Immutable Test", description="Test immutability")
        todo = Todo.from_orm(todo_data)
        session.add(todo)
        session.commit()
        session.refresh(todo)
        
        original_created_at = todo.created_at
        original_updated_at = todo.updated_at
        
        # Wait and then modify the todo
        time.sleep(0.1)
        todo.title = "Modified Title"
        todo.updated_at = datetime.now()  # This should be updated
        session.add(todo)
        session.commit()
        session.refresh(todo)
        
        # created_at should remain unchanged
        assert todo.created_at == original_created_at
        # updated_at should be changed
        assert todo.updated_at != original_updated_at
        assert todo.updated_at > original_updated_at

    def test_timestamp_format_in_api_response(self, client: TestClient):
        """Test that timestamps are properly formatted in API responses."""
        todo_data = {"title": "Format Test", "description": "Test timestamp format"}
        response = client.post("/api/v1/todo/", json=todo_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify that timestamps can be parsed as ISO format
        created_at_str = data["created_at"]
        updated_at_str = data["updated_at"]
        
        # Should be able to parse these as datetime objects
        try:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
            assert isinstance(created_at, datetime)
            assert isinstance(updated_at, datetime)
        except ValueError:
            pytest.fail("Timestamps are not in valid ISO format")

    def test_multiple_updates_increment_updated_at(self, client: TestClient):
        """Test that multiple updates continue to increment updated_at."""
        # Create a todo
        create_data = {"title": "Multi Update Test", "description": "Test multiple updates"}
        create_response = client.post("/api/v1/todo/", json=create_data)
        todo_id = create_response.json()["id"]
        
        timestamps = []
        timestamps.append(create_response.json()["updated_at"])
        
        # Perform multiple updates
        for i in range(3):
            time.sleep(0.1)  # Ensure timestamp difference
            update_data = {"title": f"Updated Title {i + 1}"}
            update_response = client.put(f"/api/v1/todo/{todo_id}", json=update_data)
            assert update_response.status_code == 200
            timestamps.append(update_response.json()["updated_at"])
        
        # Verify that each timestamp is newer than the previous
        for i in range(1, len(timestamps)):
            current_time = datetime.fromisoformat(timestamps[i].replace('Z', '+00:00'))
            previous_time = datetime.fromisoformat(timestamps[i-1].replace('Z', '+00:00'))
            assert current_time > previous_time