import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from datetime import datetime, date, timedelta
import json

from app.main import app
from app.models.user import User, PhaseEnum, EnergyProfileEnum
from app.models.goal import Goal, GoalTypeEnum, StatusEnum, PriorityEnum
from app.models.progress_log import ProgressLog
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
def test_goals(session: Session, test_user):
    """Create test goals."""
    goals = [
        Goal(
            user_id=test_user.telegram_id,
            description="Build MVP",
            type=GoalTypeEnum.MONTHLY,
            phase=PhaseEnum.MVP,
            status=StatusEnum.ACTIVE,
            priority=PriorityEnum.HIGH,
            deadline=date.today() + timedelta(days=30)
        ),
        Goal(
            user_id=test_user.telegram_id,
            description="Market Research",
            type=GoalTypeEnum.WEEKLY,
            phase=PhaseEnum.MVP,
            status=StatusEnum.ACTIVE,
            priority=PriorityEnum.MEDIUM,
            deadline=date.today() + timedelta(days=15)
        )
    ]
    for goal in goals:
        session.add(goal)
    session.commit()
    for goal in goals:
        session.refresh(goal)
    return goals

@pytest.fixture
def test_progress_logs(session: Session, test_user):
    """Create test progress logs."""
    logs = []
    for i in range(7):
        log = ProgressLog(
            user_id=test_user.telegram_id,
            date=date.today() - timedelta(days=i),
            tasks_planned=5,
            tasks_completed=3,
            mood_score=7,
            energy_level=8,
            focus_score=7,
            notes="Test progress log"
        )
        logs.append(log)
        session.add(log)
    session.commit()
    for log in logs:
        session.refresh(log)
    return logs

@pytest.fixture
def client(session: Session):
    """Create a test client with a custom session."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

class TestAIServiceIntegration:
    """Integration tests for AI service functionality."""

    def test_daily_tasks_curl_equivalent(self, client, session: Session, test_user, test_goals, test_progress_logs):
        """Test daily tasks generation matching the cURL request exactly."""
        
        # Prepare request data exactly matching the cURL request
        request_data = {
            "user_id": test_user.telegram_id,
            "energy_level": 5,
            "current_phase": test_user.current_phase.value
        }

        # Set headers exactly as in cURL
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Generate daily tasks
        response = client.post("/ai/daily-tasks", json=request_data, headers=headers)
        assert response.status_code == 200
        tasks = response.json()

        # Verify response structure
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        for task in tasks:
            assert "description" in task
            assert "estimated_duration" in task
            assert "energy_required" in task
            assert "priority" in task
            assert isinstance(task["estimated_duration"], int)
            assert task["energy_required"] in ["Low", "Medium", "High"]
            assert task["priority"] in ["Low", "Medium", "High"]

        # Test with non-existent user
        invalid_data = request_data.copy()
        invalid_data["user_id"] = "non_existent_user"
        response = client.post("/ai/daily-tasks", json=invalid_data, headers=headers)
        assert response.status_code == 404
        assert "user not found" in response.json()["detail"].lower()

        # Test with invalid energy level
        invalid_data = request_data.copy()
        invalid_data["energy_level"] = 11  # Should be 1-10
        response = client.post("/ai/daily-tasks", json=invalid_data, headers=headers)
        assert response.status_code == 422
        assert "energy_level" in response.json()["detail"][0]["loc"]

        # Test with invalid phase
        invalid_data = request_data.copy()
        invalid_data["current_phase"] = "InvalidPhase"
        response = client.post("/ai/daily-tasks", json=invalid_data, headers=headers)
        assert response.status_code == 422
        assert "current_phase" in response.json()["detail"][0]["loc"]

    def test_daily_tasks_with_no_progress(self, client, session: Session, test_user):
        """Test daily tasks generation for a new user with no progress logs."""
        request_data = {
            "user_id": test_user.telegram_id,
            "energy_level": 5
        }
        response = client.post("/ai/daily-tasks", json=request_data)
        assert response.status_code == 200
        tasks = response.json()
        assert isinstance(tasks, list)
        assert len(tasks) > 0  # Should provide default tasks

    def test_daily_tasks_with_high_energy(self, client, session: Session, test_user, test_goals, test_progress_logs):
        """Test daily tasks generation with high energy level."""
        request_data = {
            "user_id": test_user.telegram_id,
            "energy_level": 9
        }
        response = client.post("/ai/daily-tasks", json=request_data)
        assert response.status_code == 200
        tasks = response.json()
        
        # High energy should result in more challenging tasks
        high_energy_tasks = [t for t in tasks if t["energy_required"] == "High"]
        assert len(high_energy_tasks) > 0

    def test_daily_tasks_with_low_energy(self, client, session: Session, test_user, test_goals, test_progress_logs):
        """Test daily tasks generation with low energy level."""
        request_data = {
            "user_id": test_user.telegram_id,
            "energy_level": 2
        }
        response = client.post("/ai/daily-tasks", json=request_data)
        assert response.status_code == 200
        tasks = response.json()
        
        # Low energy should result in more manageable tasks
        low_energy_tasks = [t for t in tasks if t["energy_required"] == "Low"]
        assert len(low_energy_tasks) > 0

    def test_daily_tasks_goal_alignment(self, client, session: Session, test_user, test_goals):
        """Test that generated tasks align with user's goals."""
        request_data = {
            "user_id": test_user.telegram_id,
            "energy_level": 5
        }
        response = client.post("/ai/daily-tasks", json=request_data)
        assert response.status_code == 200
        tasks = response.json()
        
        # Tasks should reference MVP or market research (from test_goals)
        goal_related_tasks = [
            t for t in tasks 
            if "mvp" in t["description"].lower() or 
               "market" in t["description"].lower() or 
               "research" in t["description"].lower()
        ]
        assert len(goal_related_tasks) > 0

    def test_goals_analysis_success(self, client, session: Session, test_user, test_goals, test_progress_logs):
        """Test goals analysis with complete data."""
        # Update goal statuses for testing
        test_goals[0].status = StatusEnum.COMPLETED
        test_goals[0].completion_percentage = 100
        test_goals[1].status = StatusEnum.ACTIVE
        test_goals[1].completion_percentage = 60
        session.commit()

        request_data = {
            "user_id": test_user.telegram_id
        }
        response = client.post("/ai/analyze-goals", json=request_data)
        assert response.status_code == 200
        analysis = response.json()

        # Verify analysis structure and content
        assert "overall_status" in analysis
        assert "completion_assessment" in analysis
        assert "key_insights" in analysis
        assert "success_patterns" in analysis
        assert "challenges" in analysis
        assert "recommendations" in analysis
        assert "priority_adjustments" in analysis
        assert "achievement_score" in analysis
        assert "focus_areas" in analysis

        # Verify analysis reflects actual goal state
        assert isinstance(analysis["achievement_score"], int)
        assert analysis["achievement_score"] >= 0
        assert analysis["achievement_score"] <= 100
        assert len(analysis["key_insights"]) > 0
        assert len(analysis["recommendations"]) > 0

    def test_goals_analysis_no_goals(self, client, session: Session, test_user):
        """Test goals analysis with no goals."""
        request_data = {
            "user_id": test_user.telegram_id
        }
        response = client.post("/ai/analyze-goals", json=request_data)
        assert response.status_code == 200
        analysis = response.json()

        # Should provide meaningful analysis even with no goals
        assert analysis["overall_status"] in ["Needs Attention", "Needs Immediate Attention", "Average"]
        print("Key insights:", analysis["key_insights"])
        print("Recommendations:", analysis["recommendations"])
        # Check for no goals message in key insights
        has_no_goals_message = any(
            "no goals" in insight.lower() or
            "no entrepreneurial goals" in insight.lower() or
            "absence of goals" in insight.lower()
            for insight in analysis["key_insights"]
        )

        # Check for goal setting recommendation
        has_goal_setting_rec = any(
            "define" in rec.lower() and "goals" in rec.lower() or
            "set" in rec.lower() and "goals" in rec.lower() or
            "create" in rec.lower() and "goals" in rec.lower()
            for rec in analysis["recommendations"]
        )

        assert has_no_goals_message or has_goal_setting_rec

    def test_goals_analysis_all_completed(self, client, session: Session, test_user, test_goals):
        """Test goals analysis with all goals completed."""
        # Mark all goals as completed
        for goal in test_goals:
            goal.status = StatusEnum.COMPLETED
            goal.completion_percentage = 100
        session.commit()

        request_data = {
            "user_id": test_user.telegram_id
        }
        response = client.post("/ai/analyze-goals", json=request_data)
        assert response.status_code == 200
        analysis = response.json()

        # Should reflect excellent progress
        assert analysis["overall_status"] in ["Excellent", "Good"]
        assert analysis["completion_assessment"] in ["Ahead", "On Track"]
        assert analysis["achievement_score"] > 80  # High score for all completed

    def test_goals_analysis_invalid_user(self, client):
        """Test goals analysis with invalid user ID."""
        request_data = {
            "user_id": "non_existent_user"
        }
        response = client.post("/ai/analyze-goals", json=request_data)
        assert response.status_code == 404
        assert "user not found" in response.json()["detail"].lower()

    def test_goals_analysis_with_progress_trend(self, client, session: Session, test_user, test_goals, test_progress_logs):
        """Test goals analysis with progress trend data."""
        # Update progress logs to show improvement
        for i, log in enumerate(test_progress_logs):
            log.tasks_completed = 2 + i  # Increasing completion trend
        session.commit()

        request_data = {
            "user_id": test_user.telegram_id
        }
        response = client.post("/ai/analyze-goals", json=request_data)
        assert response.status_code == 200
        analysis = response.json()

        # Should mention positive trend
        trend_mentioned = any(
            "improving" in insight.lower() or 
            "progress" in insight.lower() or 
            "increasing" in insight.lower() 
            for insight in analysis["key_insights"]
        )
        assert trend_mentioned