"""Test utilities and helper functions."""

from typing import Dict, Any
from fastapi.testclient import TestClient


def create_test_todo(client: TestClient, todo_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Helper function to create a test todo and return the response data."""
    if todo_data is None:
        todo_data = {
            "title": "Test Todo",
            "description": "Test description"
        }
    
    response = client.post("/api/v1/todo/", json=todo_data)
    assert response.status_code == 200
    return response.json()


def assert_todo_matches(actual_todo: Dict[str, Any], expected_data: Dict[str, Any]) -> None:
    """Helper function to assert todo data matches expectations."""
    for key, value in expected_data.items():
        assert actual_todo[key] == value


def create_multiple_todos(client: TestClient, count: int = 3) -> list[Dict[str, Any]]:
    """Helper function to create multiple test todos."""
    todos = []
    for i in range(count):
        todo_data = {
            "title": f"Test Todo {i + 1}",
            "description": f"Description for todo {i + 1}"
        }
        todo = create_test_todo(client, todo_data)
        todos.append(todo)
    return todos 