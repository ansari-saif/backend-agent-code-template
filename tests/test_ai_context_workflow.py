import pytest
from datetime import datetime, date, timedelta
from fastapi import status
from sqlmodel import Session, select

from app.models.user import User, PhaseEnum, EnergyProfileEnum
from app.models.goal import Goal, PriorityEnum, StatusEnum
from app.schemas.goal import GoalTypeEnum
from app.models.task import Task, TaskPriorityEnum, CompletionStatusEnum, EnergyRequiredEnum
from app.models.job_metrics import JobMetrics
from app.models.progress_log import ProgressLog
from app.models.ai_context import AIContext

@pytest.mark.integration
def test_complete_ai_context_workflow(client, session: Session):
    """
    Test the complete workflow:
    1. Create a user
    2. Add goals
    3. Add tasks
    4. Add job metrics
    5. Add progress logs
    6. Call AI context API
    7. Verify auto-generated context
    """
    
    # 1. Create a user
    user = User(
        telegram_id="test_workflow_user",
        name="John Developer",
        current_phase=PhaseEnum.MVP,
        energy_profile=EnergyProfileEnum.MORNING,
        onboarding_complete=True,
        quit_job_target=date.today() + timedelta(days=180)
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # 2. Add goals
    goals = [
        Goal(
            user_id=user.telegram_id,
            type=GoalTypeEnum.MONTHLY,
            description="Launch MVP of SaaS Product",
            priority=PriorityEnum.HIGH,
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.MVP,
            completion_percentage=75,
            deadline=date.today() + timedelta(days=30)
        ),
        Goal(
            user_id=user.telegram_id,
            type=GoalTypeEnum.MONTHLY,
            description="Acquire First 5 Beta Users",
            priority=PriorityEnum.MEDIUM,
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.MVP,
            completion_percentage=30,
            deadline=date.today() + timedelta(days=45)
        ),
        Goal(
            user_id=user.telegram_id,
            type=GoalTypeEnum.WEEKLY,
            description="Set Up Payment Processing",
            priority=PriorityEnum.HIGH,
            status=StatusEnum.COMPLETED,
            phase=PhaseEnum.MVP,
            completion_percentage=100,
            deadline=date.today() - timedelta(days=5)
        )
    ]
    for goal in goals:
        session.add(goal)
    session.commit()

    # 3. Add tasks
    tasks = [
        Task(
            user_id=user.telegram_id,
            description="Implement User Authentication",
            priority=TaskPriorityEnum.HIGH,
            completion_status=CompletionStatusEnum.COMPLETED,
            energy_required=EnergyRequiredEnum.HIGH,
            estimated_duration=180,
            goal_id=goals[0].goal_id,
            completed_at=datetime.utcnow() - timedelta(days=3)
        ),
        Task(
            user_id=user.telegram_id,
            description="Design Dashboard UI",
            priority=TaskPriorityEnum.MEDIUM,
            completion_status=CompletionStatusEnum.IN_PROGRESS,
            energy_required=EnergyRequiredEnum.MEDIUM,
            estimated_duration=120,
            goal_id=goals[0].goal_id,
            started_at=datetime.utcnow() - timedelta(days=1)
        ),
        Task(
            user_id=user.telegram_id,
            description="Write API Documentation",
            priority=TaskPriorityEnum.LOW,
            completion_status=CompletionStatusEnum.PENDING,
            energy_required=EnergyRequiredEnum.LOW,
            estimated_duration=90,
            goal_id=goals[0].goal_id
        ),
        Task(
            user_id=user.telegram_id,
            description="Set Up Stripe Integration",
            priority=TaskPriorityEnum.HIGH,
            completion_status=CompletionStatusEnum.COMPLETED,
            energy_required=EnergyRequiredEnum.HIGH,
            estimated_duration=240,
            goal_id=goals[2].goal_id,
            completed_at=datetime.utcnow() - timedelta(days=5)
        )
    ]
    for task in tasks:
        session.add(task)
    session.commit()

    # 4. Add job metrics
    job_metrics = JobMetrics(
        user_id=user.telegram_id,
        current_salary=95000,
        startup_revenue=2500,
        monthly_expenses=3500,
        runway_months=8,
        stress_level=6,
        job_satisfaction=5,
        quit_readiness_score=70,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(job_metrics)
    session.commit()

    # 5. Add progress logs (last 7 days)
    progress_logs = []
    for i in range(7):
        log = ProgressLog(
            user_id=user.telegram_id,
            date=date.today() - timedelta(days=i),
            tasks_planned=5,
            tasks_completed=4 if i % 2 == 0 else 3,  # Alternate between 3 and 4 completed tasks
            mood_score=7 if i % 2 == 0 else 6,
            energy_level=8 if i < 3 else 7,  # Higher energy in recent days
            focus_score=7,
            created_at=datetime.utcnow() - timedelta(days=i)
        )
        progress_logs.append(log)
        session.add(log)
    session.commit()

    # 6. Call AI context API
    response = client.post(
        "/ai-context/",
        json={"user_id": user.telegram_id}
    )

    # 7. Verify response
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    # Basic validation
    assert data["user_id"] == user.telegram_id
    assert data["context_id"] is not None
    assert all(key in data for key in [
        "behavior_patterns",
        "productivity_insights",
        "motivation_triggers",
        "stress_indicators",
        "optimal_work_times"
    ])

    # Validate behavior patterns
    behavior = eval(data["behavior_patterns"])
    assert isinstance(behavior, dict)
    assert behavior["productivity_style"] == "focused"  # Should be focused due to MORNING energy profile
    assert "09:00-12:00" in behavior["peak_hours"]  # Should include morning hours
    assert behavior["work_consistency"] == "high"  # Should be high due to regular progress logs
    assert behavior["task_completion_rate"] == 50.0  # 2 completed out of 4 tasks

    # Validate productivity insights
    insights = eval(data["productivity_insights"])
    assert isinstance(insights, dict)
    assert "overall_status" in insights
    assert "key_insights" in insights
    assert isinstance(insights["key_insights"], list)

    # Validate motivation triggers
    triggers = eval(data["motivation_triggers"])
    assert isinstance(triggers, dict)
    assert "strengths" in triggers
    assert "achievement_patterns" in triggers
    assert isinstance(triggers["strengths"], list)

    # Validate stress indicators
    stress = eval(data["stress_indicators"])
    assert isinstance(stress, dict)
    assert stress["risk_level"] in ["Low", "Medium", "High"]
    assert isinstance(stress["current_stressors"], list)

    # Validate optimal work times
    work_times = eval(data["optimal_work_times"])
    assert isinstance(work_times, list)
    assert len(work_times) >= 2  # Should have at least morning and afternoon slots
    assert any("09:00" in time for time in work_times)  # Should include morning slot due to MORNING profile

    # Verify database persistence
    db_context = session.exec(
        select(AIContext).where(AIContext.user_id == user.telegram_id)
    ).first()
    assert db_context is not None
    assert db_context.context_id == data["context_id"]

    # Verify timestamps
    assert db_context.created_at is not None
    assert db_context.updated_at is not None
    assert db_context.last_updated is not None