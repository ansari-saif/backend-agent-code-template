import pytest
from datetime import datetime, date, timedelta
from fastapi import status
from sqlmodel import Session, select

from app.models.user import User, PhaseEnum, EnergyProfileEnum
from app.models.goal import Goal, PriorityEnum, StatusEnum
from app.models.task import Task, TaskPriorityEnum, CompletionStatusEnum, EnergyRequiredEnum
from app.models.job_metrics import JobMetrics
from app.models.progress_log import ProgressLog
from app.models.ai_context import AIContext
from app.services.ai_service import AIService

@pytest.fixture
def test_user(session: Session):
    """Create a test user with complete profile."""
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
    """Create test goals for the user."""
    goals = [
        Goal(
            user_id=test_user.telegram_id,
            description="Launch MVP product",
            priority=PriorityEnum.HIGH,
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.MVP,
            completion_percentage=60,
            target_date=date.today() + timedelta(days=30)
        ),
        Goal(
            user_id=test_user.telegram_id,
            description="Get 10 beta users",
            priority=PriorityEnum.MEDIUM,
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.MVP,
            completion_percentage=40,
            target_date=date.today() + timedelta(days=45)
        )
    ]
    for goal in goals:
        session.add(goal)
    session.commit()
    for goal in goals:
        session.refresh(goal)
    return goals

@pytest.fixture
def test_tasks(session: Session, test_user, test_goals):
    """Create test tasks for the user."""
    tasks = [
        Task(
            user_id=test_user.telegram_id,
            description="Implement user authentication",
            priority=TaskPriorityEnum.HIGH,
            completion_status=CompletionStatusEnum.COMPLETED,
            energy_required=EnergyRequiredEnum.HIGH,
            estimated_duration=120,
            goal_id=test_goals[0].goal_id
        ),
        Task(
            user_id=test_user.telegram_id,
            description="Design landing page",
            priority=TaskPriorityEnum.MEDIUM,
            completion_status=CompletionStatusEnum.IN_PROGRESS,
            energy_required=EnergyRequiredEnum.MEDIUM,
            estimated_duration=90,
            goal_id=test_goals[0].goal_id
        )
    ]
    for task in tasks:
        session.add(task)
    session.commit()
    for task in tasks:
        session.refresh(task)
    return tasks

@pytest.fixture
def test_job_metrics(session: Session, test_user):
    """Create test job metrics for the user."""
    metrics = JobMetrics(
        user_id=test_user.telegram_id,
        current_salary=120000,
        startup_revenue=3000,
        monthly_expenses=4000,
        runway_months=6,
        stress_level=7,
        job_satisfaction=5,
        quit_readiness_score=65
    )
    session.add(metrics)
    session.commit()
    session.refresh(metrics)
    return metrics

@pytest.fixture
def test_progress_logs(session: Session, test_user):
    """Create test progress logs for the user."""
    logs = [
        ProgressLog(
            user_id=test_user.telegram_id,
            tasks_planned=5,
            tasks_completed=4,
            mood_score=8,
            energy_level=7,
            focus_score=8,
            created_at=datetime.utcnow() - timedelta(days=i)
        )
        for i in range(7)  # Last 7 days
    ]
    for log in logs:
        session.add(log)
    session.commit()
    for log in logs:
        session.refresh(log)
    return logs

@pytest.mark.integration
async def test_auto_generate_ai_context(
    client,
    session: Session,
    test_user,
    test_goals,
    test_tasks,
    test_job_metrics,
    test_progress_logs,
    monkeypatch
):
    """Test that AI context is automatically generated with rich insights."""
    
    # Mock the AI service to return deterministic results
    class MockAIService(AIService):
        async def analyze_goals(self, goals, progress_logs=None):
            return {
                "overall_status": "Good",
                "completion_assessment": "On Track",
                "key_insights": ["Making steady progress", "Good goal prioritization"],
                "success_patterns": ["Regular updates", "Clear milestones"],
                "challenges": ["Time management"],
                "recommendations": ["Focus on MVP completion"],
                "priority_adjustments": ["Maintain current priorities"],
                "achievement_score": 75,
                "focus_areas": ["Product development", "User acquisition"]
            }
        
        async def analyze_career_transition_readiness(self, user, job_metrics):
            return {
                "financial_readiness": "Medium",
                "personal_readiness": "High",
                "overall_recommendation": "Wait",
                "risk_level": "Medium",
                "key_strengths": ["Consistent progress", "Clear planning"],
                "concerns": ["Revenue growth needed"],
                "action_items": ["Increase MRR", "Build buffer"],
                "timeline_recommendation": "3-6 months",
                "confidence_score": 70
            }

    # Patch the AI service
    monkeypatch.setattr("app.services.ai_context_service.AIService", MockAIService)

    # Call the AI context creation endpoint
    response = client.post(
        "/ai-context/",
        json={"user_id": test_user.telegram_id}
    )

    # Verify response
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    
    # Verify AI context was created
    assert data["user_id"] == test_user.telegram_id
    assert data["context_id"] is not None
    
    # Verify behavior patterns were generated
    behavior_patterns = eval(data["behavior_patterns"])  # Convert JSON string to dict
    assert isinstance(behavior_patterns, dict)
    assert "productivity_style" in behavior_patterns
    assert "peak_hours" in behavior_patterns
    
    # Verify productivity insights were generated
    assert data["productivity_insights"] is not None
    insights = eval(data["productivity_insights"])
    assert isinstance(insights, dict)
    assert "overall_status" in insights
    assert "key_insights" in insights
    
    # Verify motivation triggers were generated
    assert data["motivation_triggers"] is not None
    triggers = eval(data["motivation_triggers"])
    assert isinstance(triggers, dict)
    assert "strengths" in triggers
    
    # Verify stress indicators were generated
    assert data["stress_indicators"] is not None
    stress = eval(data["stress_indicators"])
    assert isinstance(stress, dict)
    assert "risk_level" in stress
    
    # Verify optimal work times were generated
    assert data["optimal_work_times"] is not None
    work_times = eval(data["optimal_work_times"])
    assert isinstance(work_times, list)
    assert len(work_times) > 0

    # Verify the AI context was stored in the database
    db_context = session.exec(
        select(AIContext).where(AIContext.user_id == test_user.telegram_id)
    ).first()
    assert db_context is not None
    assert db_context.context_id == data["context_id"]
