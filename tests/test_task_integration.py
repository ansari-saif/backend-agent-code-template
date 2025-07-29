import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from datetime import datetime, timedelta, date
from dateutil.parser import parse

from app.main import app
from app.models.user import User, PhaseEnum, EnergyProfileEnum
from app.models.goal import Goal, GoalTypeEnum, StatusEnum, PriorityEnum
from app.models.task import Task, TaskPriorityEnum, CompletionStatusEnum, EnergyRequiredEnum
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
def test_goal(session: Session, test_user):
    """Create a test goal."""
    goal = Goal(
        user_id=test_user.telegram_id,
        type=GoalTypeEnum.MONTHLY,
        description="Test Goal",
        phase=PhaseEnum.MVP,
        priority=PriorityEnum.HIGH,
        completion_percentage=0.0
    )
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal

@pytest.fixture
def client(session: Session):
    """Create a test client with a custom session."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

class TestTaskIntegration:
    """Integration tests for Task functionality."""

    def test_task_lifecycle(self, client, session: Session, test_user, test_goal):
        """Test complete task lifecycle: create, read, update, delete."""
        
        # 1. Create a new task
        task_data = {
            "user_id": test_user.telegram_id,
            "goal_id": test_goal.goal_id,
            "description": "Implement user authentication",
            "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
            "priority": TaskPriorityEnum.HIGH,
            "energy_required": EnergyRequiredEnum.HIGH,
            "estimated_duration": 120,  # 2 hours
            "ai_generated": False
        }
        
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 201
        created_task = response.json()
        assert created_task["description"] == task_data["description"]
        assert created_task["priority"] == task_data["priority"]
        task_id = created_task["task_id"]

        # 2. Read the created task
        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        retrieved_task = response.json()
        assert retrieved_task == created_task

        # 3. Update the task
        update_data = {
            "completion_status": CompletionStatusEnum.IN_PROGRESS,
            "actual_duration": 30,  # 30 minutes spent so far
            "priority": TaskPriorityEnum.URGENT
        }
        response = client.put(f"/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        updated_task = response.json()
        assert updated_task["completion_status"] == CompletionStatusEnum.IN_PROGRESS
        assert updated_task["actual_duration"] == 30
        assert updated_task["priority"] == TaskPriorityEnum.URGENT

        # 4. Complete the task
        response = client.patch(f"/tasks/{task_id}/complete")
        assert response.status_code == 200
        completed_task = response.json()
        assert completed_task["completion_status"] == CompletionStatusEnum.COMPLETED

        # 5. Delete the task
        response = client.delete(f"/tasks/{task_id}")
        assert response.status_code == 204

        # Verify deletion
        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 404

    def test_task_filtering_and_listing(self, client, session: Session, test_user, test_goal):
        """Test task filtering and listing features."""
        
        # Create multiple tasks with different statuses and deadlines
        tasks_data = [
            {
                "user_id": test_user.telegram_id,
                "goal_id": test_goal.goal_id,
                "description": "Task 1 - Due Today",
                "deadline": datetime.now().isoformat(),
                "priority": TaskPriorityEnum.HIGH,
                "completion_status": CompletionStatusEnum.PENDING
            },
            {
                "user_id": test_user.telegram_id,
                "goal_id": test_goal.goal_id,
                "description": "Task 2 - In Progress",
                "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
                "priority": TaskPriorityEnum.MEDIUM,
                "completion_status": CompletionStatusEnum.IN_PROGRESS
            },
            {
                "user_id": test_user.telegram_id,
                "goal_id": test_goal.goal_id,
                "description": "Task 3 - Completed",
                "deadline": (datetime.now() - timedelta(days=1)).isoformat(),
                "priority": TaskPriorityEnum.LOW,
                "completion_status": CompletionStatusEnum.COMPLETED
            }
        ]

        created_tasks = []
        for task_data in tasks_data:
            response = client.post("/tasks/", json=task_data)
            assert response.status_code == 201
            created_tasks.append(response.json())

        # Test getting all user tasks
        response = client.get(f"/tasks/user/{test_user.telegram_id}")
        assert response.status_code == 200
        user_tasks = response.json()
        assert len(user_tasks) == 3

        # Test getting pending tasks
        response = client.get(f"/tasks/user/{test_user.telegram_id}/pending")
        assert response.status_code == 200
        pending_tasks = response.json()
        assert len(pending_tasks) == 2  # PENDING and IN_PROGRESS tasks

        # Test getting today's tasks
        response = client.get(f"/tasks/user/{test_user.telegram_id}/today")
        assert response.status_code == 200
        today_tasks = response.json()
        assert len(today_tasks) == 1  # Only one task is due today

        # Test filtering by goal
        response = client.get("/tasks/", params={"goal_id": test_goal.goal_id})
        assert response.status_code == 200
        goal_tasks = response.json()
        assert len(goal_tasks) == 3

        # Test filtering by completion status
        response = client.get("/tasks/", params={"completion_status": CompletionStatusEnum.COMPLETED.value})
        assert response.status_code == 200
        completed_tasks = response.json()
        assert len(completed_tasks) == 1

    def test_task_validation(self, client, session: Session, test_user, test_goal):
        """Test task validation rules."""
        
        # Test invalid user
        invalid_task = {
            "user_id": "non_existent_user",
            "description": "Test task",
            "priority": TaskPriorityEnum.HIGH
        }
        response = client.post("/tasks/", json=invalid_task)
        assert response.status_code == 404

        # Test invalid goal
        invalid_goal_task = {
            "user_id": test_user.telegram_id,
            "goal_id": 99999,  # Non-existent goal
            "description": "Test task",
            "priority": TaskPriorityEnum.HIGH
        }
        response = client.post("/tasks/", json=invalid_goal_task)
        assert response.status_code == 404

        # Test goal-user mismatch
        other_user = User(
            telegram_id="other_user_123",
            name="Other User",
            current_phase=PhaseEnum.MVP,
            energy_profile=EnergyProfileEnum.MORNING,
            onboarding_complete=True
        )
        session.add(other_user)
        session.commit()

        mismatched_task = {
            "user_id": other_user.telegram_id,
            "goal_id": test_goal.goal_id,  # Goal belongs to test_user
            "description": "Test task",
            "priority": TaskPriorityEnum.HIGH
        }
        response = client.post("/tasks/", json=mismatched_task)
        assert response.status_code == 400

        # Test invalid task update
        task_data = {
            "user_id": test_user.telegram_id,
            "description": "Valid task",
            "priority": TaskPriorityEnum.HIGH
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 201
        task_id = response.json()["task_id"]

        invalid_update = {
            "estimated_duration": -30  # Invalid: negative duration
        }
        response = client.put(f"/tasks/{task_id}", json=invalid_update)
        assert response.status_code == 422

    def test_task_goal_relationship(self, client, session: Session, test_user, test_goal):
        """Test task-goal relationship and updates."""
        
        # Create a task linked to a goal
        task_data = {
            "user_id": test_user.telegram_id,
            "goal_id": test_goal.goal_id,
            "description": "Goal-related task",
            "priority": TaskPriorityEnum.HIGH
        }
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 201
        task_id = response.json()["task_id"]

        # Create another goal
        new_goal = Goal(
            user_id=test_user.telegram_id,
            type=GoalTypeEnum.WEEKLY,
            description="Another Goal",
            phase=PhaseEnum.MVP,
            priority=PriorityEnum.MEDIUM
        )
        session.add(new_goal)
        session.commit()

        # Update task to link to new goal
        update_data = {
            "goal_id": new_goal.goal_id
        }
        response = client.put(f"/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        updated_task = response.json()
        assert updated_task["goal_id"] == new_goal.goal_id

        # Remove goal association
        update_data = {
            "goal_id": None
        }
        response = client.put(f"/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        updated_task = response.json()
        assert updated_task["goal_id"] is None

    def test_task_complex_filtering(self, client, session: Session, test_user, test_goal):
        """Test task filtering with multiple query parameters."""
        
        # Create multiple tasks with different properties
        tasks_data = [
            {
                "user_id": test_user.telegram_id,
                "goal_id": test_goal.goal_id,
                "description": "Task 1",
                "deadline": datetime.now().isoformat(),
                "priority": TaskPriorityEnum.HIGH,
                "completion_status": CompletionStatusEnum.PENDING
            },
            {
                "user_id": test_user.telegram_id,
                "goal_id": test_goal.goal_id,
                "description": "Task 2",
                "deadline": datetime.now().isoformat(),
                "priority": TaskPriorityEnum.MEDIUM,
                "completion_status": CompletionStatusEnum.IN_PROGRESS
            }
        ]

        # Create tasks
        created_tasks = []
        for task_data in tasks_data:
            response = client.post("/tasks/", json=task_data)
            assert response.status_code == 201
            created_tasks.append(response.json())

        # Test filtering with all query parameters
        query_params = {
            "skip": 0,
            "limit": 100,
            "user_id": test_user.telegram_id,
            "goal_id": test_goal.goal_id,
            "completion_status": CompletionStatusEnum.PENDING.value
        }
        
        response = client.get("/tasks/", params=query_params)
        assert response.status_code == 200
        filtered_tasks = response.json()
        
        # Should return only the first task (PENDING status)
        assert len(filtered_tasks) == 1
        assert filtered_tasks[0]["description"] == "Task 1"
        assert filtered_tasks[0]["completion_status"] == CompletionStatusEnum.PENDING.value

        # Test with non-existent user_id
        query_params["user_id"] = "non_existent_user"
        response = client.get("/tasks/", params=query_params)
        assert response.status_code == 200
        assert len(response.json()) == 0

        # Test with non-existent goal_id
        query_params["user_id"] = test_user.telegram_id
        query_params["goal_id"] = 99999
        response = client.get("/tasks/", params=query_params)
        assert response.status_code == 200
        assert len(response.json()) == 0

        # Test with invalid completion_status
        query_params["goal_id"] = test_goal.goal_id
        query_params["completion_status"] = "invalid_status"
        response = client.get("/tasks/", params=query_params)
        assert response.status_code == 422  # Should return validation error

        # Test pagination
        query_params["completion_status"] = CompletionStatusEnum.PENDING.value
        query_params["limit"] = 1
        response = client.get("/tasks/", params=query_params)
        assert response.status_code == 200
        assert len(response.json()) <= 1  # Should respect the limit

    def test_task_comprehensive_update(self, client, session: Session, test_user, test_goal):
        """Test comprehensive task update with all possible fields."""
        
        # First, create a task to update
        initial_task = {
            "user_id": test_user.telegram_id,
            "goal_id": test_goal.goal_id,
            "description": "Initial task description",
            "deadline": datetime.now().isoformat(),
            "priority": TaskPriorityEnum.MEDIUM,
            "ai_generated": True,
            "completion_status": CompletionStatusEnum.PENDING,
            "estimated_duration": 60,
            "actual_duration": 30,
            "energy_required": EnergyRequiredEnum.MEDIUM
        }
        
        # Create the task
        response = client.post("/tasks/", json=initial_task)
        assert response.status_code == 201
        created_task = response.json()
        task_id = created_task["task_id"]

        # Create another goal for testing goal_id update
        new_goal = Goal(
            user_id=test_user.telegram_id,
            type=GoalTypeEnum.WEEKLY,
            description="Another Test Goal",
            phase=PhaseEnum.MVP,
            priority=PriorityEnum.HIGH,
            completion_percentage=0.0
        )
        session.add(new_goal)
        session.commit()
        session.refresh(new_goal)

        # Prepare update data with all fields
        update_deadline = "2024-08-05T13:40:36.538Z"
        update_data = {
            "goal_id": new_goal.goal_id,
            "description": "Updated task description",
            "deadline": update_deadline,
            "priority": TaskPriorityEnum.URGENT,
            "ai_generated": False,
            "completion_status": CompletionStatusEnum.CANCELLED,
            "estimated_duration": 2629,
            "actual_duration": 5124,
            "energy_required": EnergyRequiredEnum.LOW
        }

        # Update the task
        response = client.put(f"/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        updated_task = response.json()

        # Verify all fields were updated correctly
        assert updated_task["goal_id"] == new_goal.goal_id
        assert updated_task["description"] == update_data["description"]
        # Compare datetime objects ignoring timezone
        assert parse(updated_task["deadline"]).replace(tzinfo=None) == parse(update_deadline).replace(tzinfo=None)
        assert updated_task["priority"] == update_data["priority"]
        assert updated_task["ai_generated"] == update_data["ai_generated"]
        assert updated_task["completion_status"] == update_data["completion_status"]
        assert updated_task["estimated_duration"] == update_data["estimated_duration"]
        assert updated_task["actual_duration"] == update_data["actual_duration"]
        assert updated_task["energy_required"] == update_data["energy_required"]

        # Verify task still belongs to original user
        assert updated_task["user_id"] == test_user.telegram_id

        # Test updating non-existent task
        response = client.put("/tasks/99999", json=update_data)
        assert response.status_code == 404

        # Test updating with non-existent goal
        invalid_update = update_data.copy()
        invalid_update["goal_id"] = 99999
        response = client.put(f"/tasks/{task_id}", json=invalid_update)
        assert response.status_code == 404

        # Test updating with invalid enum values
        invalid_update = update_data.copy()
        invalid_update["priority"] = "INVALID_PRIORITY"
        response = client.put(f"/tasks/{task_id}", json=invalid_update)
        assert response.status_code == 422

        # Test updating with negative durations
        invalid_update = update_data.copy()
        invalid_update["estimated_duration"] = -100
        response = client.put(f"/tasks/{task_id}", json=invalid_update)
        assert response.status_code == 422

        invalid_update = update_data.copy()
        invalid_update["actual_duration"] = -50
        response = client.put(f"/tasks/{task_id}", json=invalid_update)
        assert response.status_code == 422

        # Test partial update (only some fields)
        partial_update = {
            "description": "Partially updated description",
            "priority": TaskPriorityEnum.HIGH
        }
        response = client.put(f"/tasks/{task_id}", json=partial_update)
        assert response.status_code == 200
        partially_updated_task = response.json()
        assert partially_updated_task["description"] == partial_update["description"]
        assert partially_updated_task["priority"] == partial_update["priority"]
        # Other fields should remain unchanged
        assert partially_updated_task["estimated_duration"] == update_data["estimated_duration"]
        assert partially_updated_task["energy_required"] == update_data["energy_required"]

        # Verify in database
        db_task = session.get(Task, task_id)
        assert db_task is not None
        assert db_task.description == partial_update["description"]
        assert db_task.priority == partial_update["priority"]

    def test_task_update_curl_equivalent(self, client, session: Session, test_user, test_goal):
        """Test task update endpoint matching the cURL request exactly."""
        
        # First, create a task to update
        initial_task = {
            "user_id": test_user.telegram_id,
            "goal_id": test_goal.goal_id,
            "description": "Initial description",
            "deadline": datetime.now().isoformat(),
            "priority": TaskPriorityEnum.MEDIUM,
            "ai_generated": True,
            "completion_status": CompletionStatusEnum.PENDING,
            "estimated_duration": 60,
            "actual_duration": 30,
            "energy_required": EnergyRequiredEnum.MEDIUM
        }
        
        # Create the task
        response = client.post("/tasks/", json=initial_task)
        assert response.status_code == 201
        created_task = response.json()
        task_id = created_task["task_id"]

        # Create a new goal with specific ID (simulating goal_id: 9466 from cURL)
        new_goal = Goal(
            user_id=test_user.telegram_id,
            type=GoalTypeEnum.WEEKLY,
            description="Test Goal for cURL equivalent",
            phase=PhaseEnum.MVP,
            priority=PriorityEnum.HIGH,
            completion_percentage=0.0
        )
        session.add(new_goal)
        session.commit()
        session.refresh(new_goal)

        # Prepare update data exactly matching the cURL request
        update_data = {
            "goal_id": new_goal.goal_id,  # Using actual goal_id from database
            "description": "string",
            "deadline": "2013-08-05T13:40:36.538Z",
            "priority": "Urgent",  # Using string value as in cURL
            "ai_generated": False,
            "completion_status": "Cancelled",  # Using string value as in cURL
            "estimated_duration": 2629,
            "actual_duration": 5124,
            "energy_required": "Low"  # Using string value as in cURL
        }

        # Set headers exactly as in cURL
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Make the PUT request
        response = client.put(f"/tasks/{task_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        updated_task = response.json()

        # Verify all fields were updated correctly
        assert updated_task["goal_id"] == new_goal.goal_id
        assert updated_task["description"] == "string"
        assert parse(updated_task["deadline"]).replace(tzinfo=None) == parse("2013-08-05T13:40:36.538Z").replace(tzinfo=None)
        assert updated_task["priority"] == TaskPriorityEnum.URGENT
        assert updated_task["ai_generated"] is False
        assert updated_task["completion_status"] == CompletionStatusEnum.CANCELLED
        assert updated_task["estimated_duration"] == 2629
        assert updated_task["actual_duration"] == 5124
        assert updated_task["energy_required"] == EnergyRequiredEnum.LOW

        # Test with non-existent task ID
        response = client.put("/tasks/99999", json=update_data, headers=headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

        # Test with non-existent goal ID
        invalid_data = update_data.copy()
        invalid_data["goal_id"] = 99999
        response = client.put(f"/tasks/{task_id}", json=invalid_data, headers=headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "Goal not found"

        # Test with invalid priority enum
        invalid_data = update_data.copy()
        invalid_data["priority"] = "INVALID_PRIORITY"
        response = client.put(f"/tasks/{task_id}", json=invalid_data, headers=headers)
        assert response.status_code == 422
        validation_error = response.json()
        assert "priority" in str(validation_error["detail"]).lower()

        # Test with invalid completion status
        invalid_data = update_data.copy()
        invalid_data["completion_status"] = "INVALID_STATUS"
        response = client.put(f"/tasks/{task_id}", json=invalid_data, headers=headers)
        assert response.status_code == 422
        validation_error = response.json()
        assert "completion_status" in str(validation_error["detail"]).lower()

        # Test with invalid energy required value
        invalid_data = update_data.copy()
        invalid_data["energy_required"] = "INVALID_ENERGY"
        response = client.put(f"/tasks/{task_id}", json=invalid_data, headers=headers)
        assert response.status_code == 422
        validation_error = response.json()
        assert "energy_required" in str(validation_error["detail"]).lower()

        # Test with negative durations
        invalid_data = update_data.copy()
        invalid_data["estimated_duration"] = -1
        response = client.put(f"/tasks/{task_id}", json=invalid_data, headers=headers)
        assert response.status_code == 422
        validation_error = response.json()
        assert "estimated_duration" in str(validation_error["detail"]).lower()

        # Verify in database
        db_task = session.get(Task, task_id)
        assert db_task is not None
        assert db_task.description == "string"
        assert db_task.priority == TaskPriorityEnum.URGENT
        assert db_task.completion_status == CompletionStatusEnum.CANCELLED
        assert db_task.energy_required == EnergyRequiredEnum.LOW
        assert db_task.estimated_duration == 2629
        assert db_task.actual_duration == 5124