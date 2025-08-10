import pytest
pytest_plugins = ("pytest_asyncio",)
pytestmark = pytest.mark.asyncio
from datetime import datetime
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from datetime import date, datetime, time
from decimal import Decimal
from app.main import app
from app.core.database import get_session
from app.models.user import User
from app.schemas.user import UserCreate, TimezoneEnum, PhaseEnum, EnergyProfileEnum
from app.models.goal import Goal
from app.schemas.goal import GoalCreate, GoalTypeEnum, StatusEnum, PriorityEnum
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskPriorityEnum, CompletionStatusEnum, EnergyRequiredEnum
from app.models.progress_log import ProgressLog
from app.schemas.progress_log import ProgressLogCreate
from app.models.ai_context import AIContext
from app.schemas.ai_context import AIContextCreate
from app.models.job_metrics import JobMetrics
from app.schemas.job_metrics import JobMetricsCreate
from app.models.prompt import Prompt
from app.schemas.prompt import PromptCreate


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create a test client with dependency override."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_todo_data():
    """Sample todo data for testing."""
    return {
        "title": "Test Todo",
        "description": "This is a test todo item",
        "is_completed": False
    }


@pytest.fixture
def sample_todo_create_data():
    """Sample todo creation data (without is_completed field)."""
    return {
        "title": "Test Todo",
        "description": "This is a test todo item"
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "telegram_id": "123456789",
        "name": "John Entrepreneur",
        "birthday": date(1990, 5, 15),
        "timezone": TimezoneEnum.IST,
        "current_phase": PhaseEnum.MVP,
        "quit_job_target": date(2024, 12, 31),
        "onboarding_complete": True,
        "morning_time": time(7, 0),
        "energy_profile": EnergyProfileEnum.MORNING
    }


@pytest.fixture
def sample_user_create_data():
    """Sample user creation data."""
    return {
        "telegram_id": "123456789",
        "name": "John Entrepreneur",
        "birthday": "1990-05-15",
        "timezone": "EST",
        "current_phase": "MVP",
        "quit_job_target": "2024-12-31",
        "onboarding_complete": True,
        "morning_time": "07:00:00",
        "energy_profile": "Morning"
    }


@pytest.fixture
def sample_goal_data():
    """Sample goal data for testing."""
    return {
        "user_id": "123456789",
        "type": GoalTypeEnum.QUARTERLY,
        "description": "Launch MVP version of the product",
        "deadline": date(2024, 6, 30),
        "status": StatusEnum.ACTIVE,
        "phase": PhaseEnum.MVP,
        "priority": PriorityEnum.HIGH,
        "completion_percentage": 25.0
    }


@pytest.fixture
def sample_goal_create_data():
    """Sample goal creation data."""
    return {
        "user_id": "123456789",
        "type": "Quarterly",
        "description": "Launch MVP version of the product",
        "deadline": "2024-06-30",
        "status": "Active",
        "phase": "MVP",
        "priority": "High",
        "completion_percentage": 25.0
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "user_id": "123456789",
        "goal_id": 1,
        "description": "Design user authentication flow",
        "priority": TaskPriorityEnum.HIGH,
        "ai_generated": True,
        "completion_status": CompletionStatusEnum.IN_PROGRESS,
        "estimated_duration": 120,
        "actual_duration": None,
        "energy_required": EnergyRequiredEnum.HIGH,
        "scheduled_for_date": date(2024, 3, 1)
    }


@pytest.fixture
def sample_task_create_data():
    """Sample task creation data."""
    return {
        "user_id": "123456789",
        "goal_id": 1,
        "description": "Design user authentication flow",
        "priority": "High",
        "ai_generated": True,
        "completion_status": CompletionStatusEnum.IN_PROGRESS.value,
        "estimated_duration": 120,
        "energy_required": "High",
        "scheduled_for_date": "2024-03-01"
    }


@pytest.fixture
def sample_progress_log_data():
    """Sample progress log data for testing."""
    return {
        "user_id": "123456789",
        "date": date(2024, 3, 1),
        "tasks_completed": 3,
        "tasks_planned": 5,
        "mood_score": 8,
        "energy_level": 7,
        "focus_score": 9,
        "daily_reflection": "Good productive day, completed authentication flow",
        "ai_insights": "User shows peak productivity in morning hours"
    }


@pytest.fixture
def sample_progress_log_create_data():
    """Sample progress log creation data."""
    return {
        "user_id": "123456789",
        "date": "2024-03-01",
        "tasks_completed": 3,
        "tasks_planned": 5,
        "mood_score": 8,
        "energy_level": 7,
        "focus_score": 9,
        "daily_reflection": "Good productive day, completed authentication flow",
        "ai_insights": "User shows peak productivity in morning hours"
    }


@pytest.fixture
def sample_ai_context_data():
    """Sample AI context data for testing."""
    return {
        "user_id": "123456789",
        "behavior_patterns": '{"type": "consistent", "peak_hours": ["07:00", "09:00"], "productivity_style": "focused_sprints"}',
        "productivity_insights": "Best performance during morning hours with 90-minute focused sessions",
        "motivation_triggers": "Progress visualization, deadline proximity, peer accountability",
        "stress_indicators": "Decreased completion rate, extended task duration, delayed starts",
        "optimal_work_times": "7:00-9:00 AM, 2:00-4:00 PM",
        "last_updated": datetime(2024, 3, 1, 10, 0)
    }


@pytest.fixture
def sample_ai_context_create_data():
    """Sample AI context creation data."""
    return {
        "user_id": "123456789",
        "behavior_patterns": '{"type": "consistent", "peak_hours": ["07:00", "09:00"]}',
        "productivity_insights": "Best performance during morning hours",
        "motivation_triggers": "Progress visualization, deadline proximity",
        "stress_indicators": "Decreased completion rate, extended task duration",
        "optimal_work_times": "7:00-9:00 AM, 2:00-4:00 PM"
    }


@pytest.fixture
def sample_job_metrics_data():
    """Sample job metrics data for testing."""
    return {
        "user_id": "123456789",
        "current_salary": Decimal("5000.00"),
        "startup_revenue": Decimal("1200.00"),
        "monthly_expenses": Decimal("3500.00"),
        "runway_months": 8.5,
        "stress_level": 7,
        "job_satisfaction": 4,
        "quit_readiness_score": 65.0,
        "last_updated": datetime(2024, 3, 1, 15, 30)
    }


@pytest.fixture
def sample_job_metrics_create_data():
    """Sample job metrics creation data."""
    return {
        "user_id": "123456789",
        "current_salary": "5000.00",
        "startup_revenue": "1200.00",
        "monthly_expenses": "3500.00",
        "runway_months": 8.5,
        "stress_level": 7,
        "job_satisfaction": 4,
        "quit_readiness_score": 65.0
    }


@pytest.fixture
def sample_prompt_data():
    """Sample prompt data for testing."""
    return {
        "user_id": "123456789",
        "prompt_text": "What should I focus on today?",
        "response_text": "Based on your goals, focus on completing the MVP tasks.",
        "created_at": datetime(2024, 3, 1, 10, 0),
        "completed_at": datetime(2024, 3, 1, 10, 5)
    }


@pytest.fixture
def sample_prompt_create_data():
    """Sample prompt creation data."""
    return {
        "user_id": "123456789",
        "prompt_text": "What should I focus on today?"
    }


@pytest.fixture
def sample_day_log_create_data(test_user):
    """Sample day log creation data."""
    current_time = datetime.utcnow()
    return {
        "user_id": test_user.telegram_id,
        "date": date.today().isoformat(),
        "start_time": current_time.isoformat(),
        "summary": "Test day log"
    }


@pytest.fixture
def test_user(session: Session, sample_user_data):
    """Create a test user in the database."""
    user = User(**sample_user_data)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def test_goal(session: Session, test_user, sample_goal_data):
    """Create a test goal in the database."""
    goal = Goal(**sample_goal_data)
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal


@pytest.fixture
def test_task(session: Session, test_user, test_goal, sample_task_data):
    """Create a test task in the database."""
    task_data = sample_task_data.copy()
    task_data["goal_id"] = test_goal.goal_id
    task = Task(**task_data)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@pytest.fixture
def test_prompt(session: Session, test_user, sample_prompt_data):
    """Create a test prompt in the database."""
    prompt = Prompt(**sample_prompt_data)
    session.add(prompt)
    session.commit()
    session.refresh(prompt)
    return prompt

# Removed test_todo fixture (Todo module deprecated)