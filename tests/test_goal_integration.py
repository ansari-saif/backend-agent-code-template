import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from datetime import date, timedelta

from app.main import app
from app.models.user import User, PhaseEnum, EnergyProfileEnum
from app.models.goal import Goal, GoalTypeEnum, StatusEnum, PriorityEnum
from app.models.task import Task
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

class TestGoalIntegration:
    """Integration tests for Goal functionality."""

    def test_goal_lifecycle(self, client, session: Session, test_user):
        """Test complete goal lifecycle: create, read, update, delete."""
        
        # 1. Create a new goal
        goal_data = {
            "user_id": test_user.telegram_id,
            "type": GoalTypeEnum.MONTHLY,
            "description": "Launch MVP product features",
            "deadline": str(date.today() + timedelta(days=30)),
            "phase": PhaseEnum.MVP,
            "priority": PriorityEnum.HIGH,
            "completion_percentage": 0.0
        }
        
        response = client.post("/goals/", json=goal_data)
        assert response.status_code == 201
        created_goal = response.json()
        assert created_goal["description"] == goal_data["description"]
        assert created_goal["type"] == goal_data["type"]
        goal_id = created_goal["goal_id"]

        # 2. Read the created goal
        response = client.get(f"/goals/{goal_id}")
        assert response.status_code == 200
        retrieved_goal = response.json()
        assert retrieved_goal == created_goal

        # 3. Update the goal
        update_data = {
            "status": StatusEnum.ACTIVE,
            "completion_percentage": 50.0,
            "priority": PriorityEnum.HIGH
        }
        response = client.put(f"/goals/{goal_id}", json=update_data)
        assert response.status_code == 200
        updated_goal = response.json()
        assert updated_goal["completion_percentage"] == 50.0
        assert updated_goal["priority"] == PriorityEnum.HIGH

        # 4. Delete the goal
        response = client.delete(f"/goals/{goal_id}")
        assert response.status_code == 204

        # Verify deletion
        response = client.get(f"/goals/{goal_id}")
        assert response.status_code == 404

    def test_user_goals_management(self, client, session: Session, test_user):
        """Test user-specific goal management features."""
        
        # Create multiple goals for the user
        goals_data = [
            {
                "user_id": test_user.telegram_id,
                "type": GoalTypeEnum.QUARTERLY,
                "description": "Scale to 1000 users",
                "deadline": str(date.today() + timedelta(days=90)),
                "phase": PhaseEnum.MVP,
                "priority": PriorityEnum.HIGH,
                "completion_percentage": 0.0
            },
            {
                "user_id": test_user.telegram_id,
                "type": GoalTypeEnum.MONTHLY,
                "description": "Implement key features",
                "deadline": str(date.today() + timedelta(days=30)),
                "phase": PhaseEnum.MVP,
                "priority": PriorityEnum.MEDIUM,
                "completion_percentage": 0.0
            },
            {
                "user_id": test_user.telegram_id,
                "type": GoalTypeEnum.WEEKLY,
                "description": "User testing",
                "deadline": str(date.today() + timedelta(days=7)),
                "phase": PhaseEnum.MVP,
                "priority": PriorityEnum.LOW,
                "status": StatusEnum.COMPLETED,
                "completion_percentage": 100.0
            }
        ]

        created_goals = []
        for goal_data in goals_data:
            response = client.post("/goals/", json=goal_data)
            assert response.status_code == 201
            created_goals.append(response.json())

        # Test getting all user goals
        response = client.get(f"/goals/user/{test_user.telegram_id}")
        assert response.status_code == 200
        user_goals = response.json()
        assert len(user_goals) == 3

        # Test getting pending goals
        response = client.get(f"/goals/user/{test_user.telegram_id}/pending")
        assert response.status_code == 200
        pending_goals = response.json()
        assert len(pending_goals) == 2  # Only non-completed goals

        # Test goal filtering
        response = client.get("/goals/", params={"user_id": test_user.telegram_id})
        assert response.status_code == 200
        filtered_goals = response.json()
        assert len(filtered_goals) == 3

    def test_goal_validation(self, client, session: Session, test_user):
        """Test goal validation rules."""
        
        # Test invalid completion percentage
        invalid_goal = {
            "user_id": test_user.telegram_id,
            "type": GoalTypeEnum.MONTHLY,
            "description": "Test goal",
            "phase": PhaseEnum.MVP,
            "completion_percentage": 150.0  # Invalid: > 100
        }
        response = client.post("/goals/", json=invalid_goal)
        assert response.status_code == 422

        # Test non-existent user
        invalid_user_goal = {
            "user_id": "non_existent_user",
            "type": GoalTypeEnum.MONTHLY,
            "description": "Test goal",
            "phase": PhaseEnum.MVP
        }
        response = client.post("/goals/", json=invalid_user_goal)
        assert response.status_code == 404

        # Test invalid goal update
        goal_data = {
            "user_id": test_user.telegram_id,
            "type": GoalTypeEnum.MONTHLY,
            "description": "Test goal",
            "phase": PhaseEnum.MVP
        }
        response = client.post("/goals/", json=goal_data)
        assert response.status_code == 201
        goal_id = response.json()["goal_id"]

        invalid_update = {
            "completion_percentage": -10.0  # Invalid: < 0
        }
        response = client.put(f"/goals/{goal_id}", json=invalid_update)
        assert response.status_code == 422

    def test_goal_phase_transitions(self, client, session: Session, test_user):
        """Test goal behavior during phase transitions."""
        
        # Create a goal in MVP phase
        goal_data = {
            "user_id": test_user.telegram_id,
            "type": GoalTypeEnum.QUARTERLY,
            "description": "MVP Phase Goal",
            "phase": PhaseEnum.MVP,
            "priority": PriorityEnum.HIGH
        }
        response = client.post("/goals/", json=goal_data)
        assert response.status_code == 201
        goal_id = response.json()["goal_id"]

        # Transition user to Growth phase
        test_user.current_phase = PhaseEnum.GROWTH
        session.add(test_user)
        session.commit()

        # Update goal phase
        update_data = {
            "phase": PhaseEnum.GROWTH,
            "description": "Transformed Growth Phase Goal"
        }
        response = client.put(f"/goals/{goal_id}", json=update_data)
        assert response.status_code == 200
        updated_goal = response.json()
        assert updated_goal["phase"] == PhaseEnum.GROWTH