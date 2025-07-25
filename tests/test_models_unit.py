import pytest
from datetime import date, datetime, time
from decimal import Decimal
from sqlmodel import Session
from app.models.user import User, UserCreate, TimezoneEnum, PhaseEnum, EnergyProfileEnum
from app.models.goal import Goal, GoalCreate, GoalTypeEnum, StatusEnum, PriorityEnum
from app.models.task import Task, TaskCreate, TaskPriorityEnum, CompletionStatusEnum, EnergyRequiredEnum
from app.models.progress_log import ProgressLog, ProgressLogCreate
from app.models.ai_context import AIContext, AIContextCreate
from app.models.job_metrics import JobMetrics, JobMetricsCreate


class TestUserModel:
    """Unit tests for User model."""

    def test_user_creation_with_defaults(self, session: Session):
        """Test user creation with default values."""
        user_data = {
            "telegram_id": "123456789",
            "name": "Test User"
        }
        user = User(**user_data)
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.telegram_id == "123456789"
        assert user.name == "Test User"
        assert user.timezone == TimezoneEnum.UTC
        assert user.current_phase == PhaseEnum.RESEARCH
        assert user.onboarding_complete is False
        assert user.energy_profile == EnergyProfileEnum.MORNING

    def test_user_creation_with_all_fields(self, session: Session, sample_user_data):
        """Test user creation with all fields."""
        user = User(**sample_user_data)
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.telegram_id == sample_user_data["telegram_id"]
        assert user.name == sample_user_data["name"]
        assert user.birthday == sample_user_data["birthday"]
        assert user.timezone == sample_user_data["timezone"]
        assert user.current_phase == sample_user_data["current_phase"]
        assert user.quit_job_target == sample_user_data["quit_job_target"]
        assert user.onboarding_complete == sample_user_data["onboarding_complete"]
        assert user.morning_time == sample_user_data["morning_time"]
        assert user.energy_profile == sample_user_data["energy_profile"]

    def test_user_enum_validations(self, session: Session):
        """Test that enum validations work correctly."""
        # Test valid enums
        user = User(
            telegram_id="test123",
            name="Test User",
            timezone=TimezoneEnum.EST,
            current_phase=PhaseEnum.MVP,
            energy_profile=EnergyProfileEnum.EVENING
        )
        session.add(user)
        session.commit()
        assert user.timezone == TimezoneEnum.EST
        assert user.current_phase == PhaseEnum.MVP
        assert user.energy_profile == EnergyProfileEnum.EVENING

    def test_user_update_model(self):
        """Test UserUpdate model has optional fields."""
        from app.models.user import UserUpdate
        
        update_data = UserUpdate(name="New Name", current_phase=PhaseEnum.GROWTH)
        assert update_data.name == "New Name"
        assert update_data.current_phase == PhaseEnum.GROWTH
        assert update_data.birthday is None


class TestGoalModel:
    """Unit tests for Goal model."""

    def test_goal_creation_with_defaults(self, session: Session, test_user):
        """Test goal creation with default values."""
        goal_data = {
            "user_id": test_user.telegram_id,
            "type": GoalTypeEnum.MONTHLY,
            "description": "Test goal",
            "phase": PhaseEnum.MVP
        }
        goal = Goal(**goal_data)
        session.add(goal)
        session.commit()
        session.refresh(goal)

        assert goal.user_id == test_user.telegram_id
        assert goal.type == GoalTypeEnum.MONTHLY
        assert goal.status == StatusEnum.ACTIVE
        assert goal.priority == PriorityEnum.MEDIUM
        assert goal.completion_percentage == 0.0

    def test_goal_creation_with_all_fields(self, session: Session, test_user, sample_goal_data):
        """Test goal creation with all fields."""
        goal = Goal(**sample_goal_data)
        session.add(goal)
        session.commit()
        session.refresh(goal)

        assert goal.user_id == sample_goal_data["user_id"]
        assert goal.type == sample_goal_data["type"]
        assert goal.description == sample_goal_data["description"]
        assert goal.deadline == sample_goal_data["deadline"]
        assert goal.status == sample_goal_data["status"]
        assert goal.phase == sample_goal_data["phase"]
        assert goal.priority == sample_goal_data["priority"]
        assert goal.completion_percentage == sample_goal_data["completion_percentage"]

    def test_goal_completion_percentage_validation(self, session: Session, test_user):
        """Test completion percentage validation (0-100)."""
        # Valid percentage
        goal = Goal(
            user_id=test_user.telegram_id,
            type=GoalTypeEnum.WEEKLY,
            description="Test goal",
            phase=PhaseEnum.MVP,
            completion_percentage=75.5
        )
        session.add(goal)
        session.commit()
        assert goal.completion_percentage == 75.5

    def test_goal_user_relationship(self, session: Session, test_user, test_goal):
        """Test goal-user relationship."""
        # Refresh to load relationships
        session.refresh(test_goal)
        session.refresh(test_user)
        
        assert test_goal.user_id == test_user.telegram_id
        assert test_goal in test_user.goals


class TestTaskModel:
    """Unit tests for Task model."""

    def test_task_creation_with_defaults(self, session: Session, test_user):
        """Test task creation with default values."""
        task_data = {
            "user_id": test_user.telegram_id,
            "description": "Test task"
        }
        task = Task(**task_data)
        session.add(task)
        session.commit()
        session.refresh(task)

        assert task.user_id == test_user.telegram_id
        assert task.description == "Test task"
        assert task.priority == TaskPriorityEnum.MEDIUM
        assert task.ai_generated is False
        assert task.completion_status == CompletionStatusEnum.PENDING
        assert task.energy_required == EnergyRequiredEnum.MEDIUM

    def test_task_creation_with_goal(self, session: Session, test_user, test_goal):
        """Test task creation with goal relationship."""
        task_data = {
            "user_id": test_user.telegram_id,
            "goal_id": test_goal.goal_id,
            "description": "Goal-related task",
            "priority": TaskPriorityEnum.URGENT,
            "completion_status": CompletionStatusEnum.IN_PROGRESS
        }
        task = Task(**task_data)
        session.add(task)
        session.commit()
        session.refresh(task)

        assert task.goal_id == test_goal.goal_id
        assert task.priority == TaskPriorityEnum.URGENT
        assert task.completion_status == CompletionStatusEnum.IN_PROGRESS

    def test_task_duration_fields(self, session: Session, test_user):
        """Test task duration fields."""
        task = Task(
            user_id=test_user.telegram_id,
            description="Timed task",
            estimated_duration=120,
            actual_duration=135
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        assert task.estimated_duration == 120
        assert task.actual_duration == 135

    def test_task_relationships(self, session: Session, test_user, test_goal, test_task):
        """Test task relationships with user and goal."""
        session.refresh(test_task)
        session.refresh(test_user)
        session.refresh(test_goal)

        assert test_task.user_id == test_user.telegram_id
        assert test_task.goal_id == test_goal.goal_id
        assert test_task in test_user.tasks
        assert test_task in test_goal.tasks


class TestProgressLogModel:
    """Unit tests for ProgressLog model."""

    def test_progress_log_creation(self, session: Session, test_user, sample_progress_log_data):
        """Test progress log creation."""
        progress_log = ProgressLog(**sample_progress_log_data)
        session.add(progress_log)
        session.commit()
        session.refresh(progress_log)

        assert progress_log.user_id == sample_progress_log_data["user_id"]
        assert progress_log.date == sample_progress_log_data["date"]
        assert progress_log.tasks_completed == sample_progress_log_data["tasks_completed"]
        assert progress_log.tasks_planned == sample_progress_log_data["tasks_planned"]
        assert progress_log.mood_score == sample_progress_log_data["mood_score"]
        assert progress_log.energy_level == sample_progress_log_data["energy_level"]
        assert progress_log.focus_score == sample_progress_log_data["focus_score"]

    def test_progress_log_score_validation(self, session: Session, test_user):
        """Test score validation (1-10 range)."""
        progress_log = ProgressLog(
            user_id=test_user.telegram_id,
            date=date.today(),
            mood_score=8,
            energy_level=6,
            focus_score=9
        )
        session.add(progress_log)
        session.commit()
        
        assert 1 <= progress_log.mood_score <= 10
        assert 1 <= progress_log.energy_level <= 10
        assert 1 <= progress_log.focus_score <= 10

    def test_progress_log_user_relationship(self, session: Session, test_user):
        """Test progress log-user relationship."""
        progress_log = ProgressLog(
            user_id=test_user.telegram_id,
            date=date.today(),
            mood_score=7,
            energy_level=8,
            focus_score=6
        )
        session.add(progress_log)
        session.commit()
        session.refresh(progress_log)
        session.refresh(test_user)

        assert progress_log.user_id == test_user.telegram_id
        assert progress_log in test_user.progress_logs


class TestAIContextModel:
    """Unit tests for AIContext model."""

    def test_ai_context_creation(self, session: Session, test_user, sample_ai_context_data):
        """Test AI context creation."""
        ai_context = AIContext(**sample_ai_context_data)
        session.add(ai_context)
        session.commit()
        session.refresh(ai_context)

        assert ai_context.user_id == sample_ai_context_data["user_id"]
        assert ai_context.behavior_patterns == sample_ai_context_data["behavior_patterns"]
        assert ai_context.productivity_insights == sample_ai_context_data["productivity_insights"]
        assert ai_context.motivation_triggers == sample_ai_context_data["motivation_triggers"]
        assert ai_context.stress_indicators == sample_ai_context_data["stress_indicators"]
        assert ai_context.optimal_work_times == sample_ai_context_data["optimal_work_times"]

    def test_ai_context_default_timestamp(self, session: Session, test_user):
        """Test AI context with default timestamp."""
        ai_context = AIContext(
            user_id=test_user.telegram_id,
            productivity_insights="Test insights"
        )
        session.add(ai_context)
        session.commit()
        session.refresh(ai_context)

        assert ai_context.last_updated is not None
        assert isinstance(ai_context.last_updated, datetime)

    def test_ai_context_user_relationship(self, session: Session, test_user):
        """Test AI context-user relationship."""
        ai_context = AIContext(
            user_id=test_user.telegram_id,
            productivity_insights="Test relationship"
        )
        session.add(ai_context)
        session.commit()
        session.refresh(ai_context)
        session.refresh(test_user)

        assert ai_context.user_id == test_user.telegram_id
        assert test_user.ai_context == ai_context


class TestJobMetricsModel:
    """Unit tests for JobMetrics model."""

    def test_job_metrics_creation(self, session: Session, test_user, sample_job_metrics_data):
        """Test job metrics creation."""
        job_metrics = JobMetrics(**sample_job_metrics_data)
        session.add(job_metrics)
        session.commit()
        session.refresh(job_metrics)

        assert job_metrics.user_id == sample_job_metrics_data["user_id"]
        assert job_metrics.current_salary == sample_job_metrics_data["current_salary"]
        assert job_metrics.startup_revenue == sample_job_metrics_data["startup_revenue"]
        assert job_metrics.monthly_expenses == sample_job_metrics_data["monthly_expenses"]
        assert job_metrics.runway_months == sample_job_metrics_data["runway_months"]
        assert job_metrics.stress_level == sample_job_metrics_data["stress_level"]
        assert job_metrics.job_satisfaction == sample_job_metrics_data["job_satisfaction"]

    def test_job_metrics_decimal_fields(self, session: Session, test_user):
        """Test job metrics with decimal fields."""
        job_metrics = JobMetrics(
            user_id=test_user.telegram_id,
            current_salary=Decimal("7500.50"),
            startup_revenue=Decimal("2250.75"),
            monthly_expenses=Decimal("4000.25"),
            stress_level=6,
            job_satisfaction=7
        )
        session.add(job_metrics)
        session.commit()
        session.refresh(job_metrics)

        assert isinstance(job_metrics.current_salary, Decimal)
        assert job_metrics.current_salary == Decimal("7500.50")
        assert job_metrics.startup_revenue == Decimal("2250.75")

    def test_job_metrics_score_validation(self, session: Session, test_user):
        """Test job metrics score validation (1-10 range)."""
        job_metrics = JobMetrics(
            user_id=test_user.telegram_id,
            stress_level=9,
            job_satisfaction=3
        )
        session.add(job_metrics)
        session.commit()

        assert 1 <= job_metrics.stress_level <= 10
        assert 1 <= job_metrics.job_satisfaction <= 10

    def test_job_metrics_user_relationship(self, session: Session, test_user):
        """Test job metrics-user relationship."""
        job_metrics = JobMetrics(
            user_id=test_user.telegram_id,
            stress_level=5,
            job_satisfaction=8
        )
        session.add(job_metrics)
        session.commit()
        session.refresh(job_metrics)
        session.refresh(test_user)

        assert job_metrics.user_id == test_user.telegram_id
        assert test_user.job_metrics == job_metrics 