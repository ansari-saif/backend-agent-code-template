import pytest
from datetime import datetime, date, timedelta
from app.schemas.task import (
    TaskBase, TaskCreate, TaskUpdate, TaskUpdate2,
    TaskPriorityEnum, CompletionStatusEnum, EnergyRequiredEnum
)
from app.schemas.day_log import (
    DayLogBase, DayLogCreate, DayLogUpdate, DayLogResponse
)

class TestTaskSchemas:
    """Test cases for Task-related schemas."""

    def test_task_base_schema(self):
        """Test TaskBase schema with timestamp fields."""
        current_time = datetime.utcnow()
        task_data = {
            "description": "Test task",
            "created_at": current_time,
            "updated_at": current_time,
            "started_at": None,
            "completed_at": None,
            "priority": TaskPriorityEnum.HIGH,
            "completion_status": CompletionStatusEnum.PENDING,
            "estimated_duration": 60,
            "actual_duration": None,
            "energy_required": EnergyRequiredEnum.MEDIUM
        }
        task = TaskBase(**task_data)
        
        assert task.description == "Test task"
        assert task.created_at == current_time
        assert task.updated_at == current_time
        assert task.started_at is None
        assert task.completed_at is None
        assert task.priority == TaskPriorityEnum.HIGH
        assert task.completion_status == CompletionStatusEnum.PENDING
        assert task.energy_required == EnergyRequiredEnum.MEDIUM

    def test_task_create_schema(self):
        """Test TaskCreate schema inherits correctly from TaskBase."""
        current_time = datetime.utcnow()
        task_data = {
            "description": "New task",
            "created_at": current_time,
            "updated_at": current_time,
            "priority": TaskPriorityEnum.LOW
        }
        task = TaskCreate(**task_data)
        
        assert task.description == "New task"
        assert task.created_at == current_time
        assert task.updated_at == current_time
        assert task.started_at is None  # Default value
        assert task.completed_at is None  # Default value
        assert task.priority == TaskPriorityEnum.LOW
        assert task.completion_status == CompletionStatusEnum.PENDING  # Default value

    def test_task_update_schema(self):
        """Test TaskUpdate schema with timestamp fields."""
        current_time = datetime.utcnow()
        update_data = {
            "description": "Updated task",
            "created_at": current_time,
            "updated_at": current_time,
            "started_at": current_time,
            "completed_at": None,
            "priority": TaskPriorityEnum.URGENT,
            "completion_status": CompletionStatusEnum.IN_PROGRESS
        }
        task_update = TaskUpdate(**update_data)
        
        assert task_update.description == "Updated task"
        assert task_update.created_at == current_time
        assert task_update.updated_at == current_time
        assert task_update.started_at == current_time
        assert task_update.completed_at is None
        assert task_update.priority == TaskPriorityEnum.URGENT
        assert task_update.completion_status == CompletionStatusEnum.IN_PROGRESS

    def test_task_update2_schema(self):
        """Test TaskUpdate2 schema with timestamp fields."""
        current_time = datetime.utcnow()
        update_data = {
            "description": "Updated task",
            "created_at": current_time,
            "updated_at": current_time,
            "started_at": current_time,
            "completed_at": current_time,
            "priority": TaskPriorityEnum.HIGH,
            "completion_status": CompletionStatusEnum.COMPLETED
        }
        task_update = TaskUpdate2(**update_data)
        
        assert task_update.description == "Updated task"
        assert task_update.created_at == current_time
        assert task_update.updated_at == current_time
        assert task_update.started_at == current_time
        assert task_update.completed_at == current_time
        assert task_update.priority == TaskPriorityEnum.HIGH
        assert task_update.completion_status == CompletionStatusEnum.COMPLETED

    def test_task_schema_validation(self):
        """Test validation rules for task schemas."""
        current_time = datetime.utcnow()
        
        # Test that completed_at cannot be before started_at
        with pytest.raises(ValueError):
            TaskUpdate(
                started_at=current_time,
                completed_at=datetime(2020, 1, 1),  # Date in the past
                description="Test task",
                priority=TaskPriorityEnum.HIGH,
                completion_status=CompletionStatusEnum.PENDING,
                energy_required=EnergyRequiredEnum.MEDIUM
            )
        
        # Test that created_at cannot be after updated_at
        with pytest.raises(ValueError):
            future_time = datetime(2025, 1, 1)
            past_time = datetime(2020, 1, 1)
            TaskBase(
                description="Test task",
                created_at=future_time,
                updated_at=past_time,
                priority=TaskPriorityEnum.HIGH,
                completion_status=CompletionStatusEnum.PENDING,
                energy_required=EnergyRequiredEnum.MEDIUM
            )


class TestDayLogSchemas:
    """Test cases for DayLog-related schemas."""

    def test_day_log_base_schema(self):
        """Test DayLogBase schema."""
        current_time = datetime.utcnow()
        log_data = {
            "date": date.today(),
            "start_time": current_time,
            "end_time": current_time + timedelta(hours=8),
            "summary": "Test day log",
            "highlights": "Test highlights",
            "challenges": "Test challenges",
            "learnings": "Test learnings",
            "gratitude": "Test gratitude",
            "tomorrow_plan": "Test plan",
            "weather": "Sunny",
            "location": "Home office"
        }
        day_log = DayLogBase(**log_data)
        
        assert day_log.date == date.today()
        assert day_log.start_time == current_time
        assert day_log.end_time == current_time + timedelta(hours=8)
        assert day_log.summary == "Test day log"
        assert day_log.highlights == "Test highlights"
        assert day_log.challenges == "Test challenges"
        assert day_log.learnings == "Test learnings"
        assert day_log.gratitude == "Test gratitude"
        assert day_log.tomorrow_plan == "Test plan"
        assert day_log.weather == "Sunny"
        assert day_log.location == "Home office"

    def test_day_log_create_schema(self):
        """Test DayLogCreate schema inherits correctly from DayLogBase."""
        current_time = datetime.utcnow()
        log_data = {
            "user_id": "test_user_123",
            "date": date.today(),
            "start_time": current_time,
            "summary": "Test day log"
        }
        day_log = DayLogCreate(**log_data)
        
        assert day_log.user_id == "test_user_123"
        assert day_log.date == date.today()
        assert day_log.start_time == current_time
        assert day_log.summary == "Test day log"
        assert day_log.end_time is None  # Optional field
        assert day_log.highlights is None  # Optional field
        assert day_log.challenges is None  # Optional field

    def test_day_log_update_schema(self):
        """Test DayLogUpdate schema with optional fields."""
        current_time = datetime.utcnow()
        update_data = {
            "end_time": current_time + timedelta(hours=8),
            "summary": "Updated summary",
            "highlights": "New highlights",
            "challenges": "New challenges"
        }
        day_log_update = DayLogUpdate(**update_data)
        
        assert day_log_update.end_time == current_time + timedelta(hours=8)
        assert day_log_update.summary == "Updated summary"
        assert day_log_update.highlights == "New highlights"
        assert day_log_update.challenges == "New challenges"
        assert day_log_update.date is None  # Not included in update
        assert day_log_update.start_time is None  # Not included in update

    def test_day_log_response_schema(self):
        """Test DayLogResponse schema."""
        current_time = datetime.utcnow()
        response_data = {
            "log_id": 1,
            "user_id": "test_user_123",
            "date": date.today(),
            "start_time": current_time,
            "end_time": current_time + timedelta(hours=8),
            "summary": "Test day log",
            "highlights": "Test highlights",
            "challenges": "Test challenges"
        }
        day_log_response = DayLogResponse(**response_data)
        
        assert day_log_response.log_id == 1
        assert day_log_response.user_id == "test_user_123"
        assert day_log_response.date == date.today()
        assert day_log_response.start_time == current_time
        assert day_log_response.end_time == current_time + timedelta(hours=8)
        assert day_log_response.summary == "Test day log"
        assert day_log_response.highlights == "Test highlights"
        assert day_log_response.challenges == "Test challenges"

    def test_day_log_schema_validation(self):
        """Test validation rules for day log schemas."""
        current_time = datetime.utcnow()
        
        # Test that end_time cannot be before start_time
        with pytest.raises(ValueError):
            DayLogBase(
                date=date.today(),
                start_time=current_time,
                end_time=current_time - timedelta(hours=1),  # End time before start time
                summary="Test log"
            )
        
        # Test that date cannot be in the future
        future_date = date.today() + timedelta(days=7)
        with pytest.raises(ValueError):
            DayLogBase(
                date=future_date,
                start_time=current_time,
                summary="Test log"
            )
