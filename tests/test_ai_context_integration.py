import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from datetime import datetime, timedelta, date
import json

from app.main import app
from app.models.user import User, PhaseEnum, EnergyProfileEnum
from app.models.ai_context import AIContext
from app.core.database import get_session

@pytest.fixture
def test_user(session: Session):
    """Create a test user."""
    user = User(
        telegram_id="test_user_123",
        name="Test User",
        current_phase=PhaseEnum.MVP,
        energy_profile=EnergyProfileEnum.MORNING,
        onboarding_complete=True,
        quit_job_target=date.today() + timedelta(days=180)
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture
def client(session: Session):
    """Create a test client with a custom session."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def cleanup_ai_contexts(session: Session):
    """Clean up AI contexts after each test."""
    yield
    session.query(AIContext).delete()
    session.commit()

class TestAIContextIntegration:
    """Integration tests for AI Context functionality."""

    def test_ai_context_curl_equivalent(self, client, session: Session, test_user):
        """Test AI context creation matching the cURL request exactly."""
        
        # Prepare request data exactly matching the cURL request
        context_data = {
            "user_id": test_user.telegram_id,  # Using actual user_id instead of "string"
            "behavior_patterns": json.dumps({"key": "value"}),  # Valid JSON string
            "productivity_insights": "string",
            "motivation_triggers": "string",
            "stress_indicators": "string",
            "optimal_work_times": "string",
            "last_updated": "2024-03-10T05:06:51.273Z"
        }

        # Set headers exactly as in cURL
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Create AI context
        response = client.post("/ai-context/", json=context_data, headers=headers)
        assert response.status_code == 201
        created_context = response.json()

        # Verify all fields were created correctly
        assert created_context["user_id"] == test_user.telegram_id
        assert json.loads(created_context["behavior_patterns"]) == {"key": "value"}
        assert created_context["productivity_insights"] == "string"
        assert created_context["motivation_triggers"] == "string"
        assert created_context["stress_indicators"] == "string"
        assert created_context["optimal_work_times"] == "string"
        # last_updated will be set automatically, so we don't compare it directly

        # Test creating duplicate context (should fail)
        response = client.post("/ai-context/", json=context_data, headers=headers)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

        # Test with non-existent user
        invalid_data = context_data.copy()
        invalid_data["user_id"] = "non_existent_user"
        response = client.post("/ai-context/", json=invalid_data, headers=headers)
        assert response.status_code == 404
        assert "user not found" in response.json()["detail"].lower()

        # Test with invalid JSON in behavior_patterns
        invalid_data = context_data.copy()
        invalid_data["behavior_patterns"] = "{invalid_json"
        session.query(AIContext).delete()  # Clear existing contexts
        session.commit()
        response = client.post("/ai-context/", json=invalid_data, headers=headers)
        assert response.status_code == 400
        assert "invalid json" in response.json()["detail"].lower()

        # Test retrieving the created context
        response = client.get(f"/ai-context/user/{test_user.telegram_id}")
        assert response.status_code == 404  # Should be not found after cleanup

        # Create a new context for update tests
        response = client.post("/ai-context/", json=context_data, headers=headers)
        assert response.status_code == 201
        created_context = response.json()

        # Test updating the context
        update_data = {
            "behavior_patterns": json.dumps({"key": "updated_value"}),
            "productivity_insights": "Updated insights",
            "motivation_triggers": "Updated triggers",
            "stress_indicators": "Updated indicators",
            "optimal_work_times": "Updated times"
        }
        context_id = created_context["context_id"]
        response = client.put(f"/ai-context/{context_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        updated_context = response.json()
        assert updated_context["productivity_insights"] == "Updated insights"
        assert updated_context["motivation_triggers"] == "Updated triggers"
        assert json.loads(updated_context["behavior_patterns"]) == {"key": "updated_value"}

        # Test partial update
        partial_update = {
            "productivity_insights": "Partially updated insights"
        }
        response = client.put(f"/ai-context/{context_id}", json=partial_update, headers=headers)
        assert response.status_code == 200
        partially_updated = response.json()
        assert partially_updated["productivity_insights"] == "Partially updated insights"
        # Other fields should remain unchanged
        assert partially_updated["motivation_triggers"] == "Updated triggers"

        # Test updating non-existent context
        response = client.put("/ai-context/99999", json=update_data, headers=headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        # Test deleting the context
        response = client.delete(f"/ai-context/{context_id}")
        assert response.status_code == 204

        # Verify deletion
        response = client.get(f"/ai-context/{context_id}")
        assert response.status_code == 404

    def test_ai_context_behavior_patterns(self, client, session: Session, test_user):
        """Test AI context behavior patterns specific functionality."""
        
        # Test updating behavior patterns for new user
        patterns = {
            "peak_hours": ["09:00", "14:00"],
            "productivity_style": "focused",
            "stress_response": "adaptive"
        }
        response = client.patch(
            f"/ai-context/user/{test_user.telegram_id}/patterns",
            json=patterns
        )
        assert response.status_code == 200
        updated_context = response.json()
        assert json.loads(updated_context["behavior_patterns"]) == patterns

        # Test updating existing patterns
        new_patterns = {
            "peak_hours": ["10:00", "15:00"],
            "productivity_style": "flexible"
        }
        response = client.patch(
            f"/ai-context/user/{test_user.telegram_id}/patterns",
            json=new_patterns
        )
        assert response.status_code == 200
        updated_context = response.json()
        assert json.loads(updated_context["behavior_patterns"]) == new_patterns

    def test_ai_context_insights(self, client, session: Session, test_user):
        """Test AI context productivity insights functionality."""
        
        # Create initial context
        context_data = {
            "user_id": test_user.telegram_id,
            "productivity_insights": "Initial insights",
            "behavior_patterns": json.dumps({"key": "value"})  # Valid JSON string
        }
        response = client.post("/ai-context/", json=context_data)
        assert response.status_code == 201

        # Test updating insights
        new_insights = "Updated productivity insights with detailed analysis"
        response = client.patch(
            f"/ai-context/user/{test_user.telegram_id}/insights",
            json={"insights": new_insights}  # Pass as named parameter
        )
        assert response.status_code == 200
        updated_context = response.json()
        assert updated_context["productivity_insights"] == new_insights

        # Test updating non-existent user's insights
        response = client.patch(
            "/ai-context/user/non_existent_user/insights",
            json={"insights": "Should not work"}  # Pass as named parameter
        )
        assert response.status_code == 404
        assert "user not found" in response.json()["detail"].lower()