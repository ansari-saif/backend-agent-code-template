import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import date, datetime, timedelta
from decimal import Decimal
from app.services.ai_service import AIService
from app.models.user import User, PhaseEnum, EnergyProfileEnum, TimezoneEnum
from app.models.goal import Goal, GoalTypeEnum, StatusEnum, PriorityEnum
from app.models.task import Task, TaskPriorityEnum, CompletionStatusEnum, EnergyRequiredEnum
from app.models.progress_log import ProgressLog
from app.models.ai_context import AIContext
from app.models.job_metrics import JobMetrics


@pytest.fixture
def mock_ai_service():
    """Create AI service with mocked Gemini."""
    with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-api-key'}):
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model:
                mock_instance = Mock()
                mock_model.return_value = mock_instance
                service = AIService()
                service.model = mock_instance
                return service

@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        telegram_id="123456789",
        name="John Entrepreneur",
        current_phase=PhaseEnum.MVP,
        energy_profile=EnergyProfileEnum.MORNING
    )

@pytest.fixture
def sample_progress_logs():
    """Create sample progress logs."""
    return [
        ProgressLog(
            user_id="123456789",
            date=date.today() - timedelta(days=i),
            tasks_completed=3 + i % 2,
            tasks_planned=5,
            mood_score=7 + i % 3,
            energy_level=8 - i % 2,
            focus_score=6 + i % 4
        )
        for i in range(7)
    ]

@pytest.fixture
def sample_goals():
    """Create sample goals."""
    return [
        Goal(
            goal_id=1,
            user_id="123456789",
            type=GoalTypeEnum.QUARTERLY,
            description="Launch MVP product",
            phase=PhaseEnum.MVP,
            priority=PriorityEnum.HIGH,
            status=StatusEnum.ACTIVE,
            deadline=date.today() + timedelta(days=30)
        ),
        Goal(
            goal_id=2,
            user_id="123456789",
            type=GoalTypeEnum.MONTHLY,
            description="Get first 100 users",
            phase=PhaseEnum.MVP,
            priority=PriorityEnum.MEDIUM,
            status=StatusEnum.ACTIVE
        )
    ]

@pytest.fixture
def sample_tasks():
    """Create sample tasks."""
    return [
        Task(
            task_id=1,
            user_id="123456789",
            description="Complete user authentication",
            completion_status=CompletionStatusEnum.COMPLETED,
            priority=TaskPriorityEnum.HIGH
        ),
        Task(
            task_id=2,
            user_id="123456789",
            description="Design payment flow",
            completion_status=CompletionStatusEnum.COMPLETED,
            priority=TaskPriorityEnum.MEDIUM
        )
    ]

@pytest.fixture
def sample_ai_context():
    """Create sample AI context."""
    return AIContext(
        user_id="123456789",
        behavior_patterns='{"type": "consistent", "peak_hours": ["07:00", "09:00"]}',
        productivity_insights="Peak performance in morning hours",
        motivation_triggers="Progress visualization, deadlines",
        stress_indicators="Extended task duration, missed deadlines"
    )

@pytest.fixture
def sample_job_metrics():
    """Create sample job metrics."""
    return JobMetrics(
        user_id="123456789",
        current_salary=Decimal("5000.00"),
        startup_revenue=Decimal("1500.00"),
        monthly_expenses=Decimal("3000.00"),
        runway_months=8.0,
        stress_level=6,
        job_satisfaction=4,
        quit_readiness_score=70.0
    )


class TestAIService:
    """Test suite for AI Service with Gemini integration."""


class TestDailyTaskGeneration:
    """Test daily task generation (Agent 1)."""

    @pytest.mark.asyncio
    async def test_generate_daily_tasks_success(self, mock_ai_service, sample_user, sample_progress_logs, sample_goals):
        """Test successful daily task generation."""
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = '''```json
        [
            {
                "description": "Implement user registration API endpoint",
                "estimated_duration": 90,
                "energy_required": "High",
                "priority": "High"
            },
            {
                "description": "Design database schema for user profiles",
                "estimated_duration": 60,
                "energy_required": "Medium",
                "priority": "Medium"
            },
            {
                "description": "Set up automated testing pipeline",
                "estimated_duration": 120,
                "energy_required": "Low",
                "priority": "Low"
            }
        ]
        ```'''
        mock_ai_service.model.generate_content.return_value = mock_response

        tasks = await mock_ai_service.generate_daily_tasks(
            user=sample_user,
            recent_progress=sample_progress_logs,
            pending_goals=sample_goals,
            today_energy_level=8
        )

        assert len(tasks) == 3
        assert tasks[0]["description"] == "Implement user registration API endpoint"
        assert tasks[0]["estimated_duration"] == 90
        assert tasks[0]["energy_required"] == "High"
        assert tasks[0]["priority"] == "High"

        # Verify the call was made with correct prompt context
        mock_ai_service.model.generate_content.assert_called_once()
        call_args = mock_ai_service.model.generate_content.call_args[0][0]
        assert "PhaseEnum.MVP" in call_args  # Updated to check for enum representation
        assert "Energy Level: 8/10" in call_args

    @pytest.mark.asyncio
    async def test_generate_daily_tasks_ai_failure(self, mock_ai_service, sample_user, sample_progress_logs, sample_goals):
        """Test daily task generation when AI fails."""
        # Mock AI failure
        mock_ai_service.model.generate_content.side_effect = Exception("AI service error")

        tasks = await mock_ai_service.generate_daily_tasks(
            user=sample_user,
            recent_progress=sample_progress_logs,
            pending_goals=sample_goals
        )

        # Should return fallback tasks
        assert len(tasks) == 2
        assert "Review and prioritize today's goals" in tasks[0]["description"]
        assert "Work on highest priority project task" in tasks[1]["description"]


class TestMotivationGeneration:
    """Test motivation message generation (Agent 2)."""

    @pytest.mark.asyncio
    async def test_generate_motivation_message_success(self, mock_ai_service, sample_user, sample_ai_context, sample_tasks):
        """Test successful motivation message generation."""
        mock_response = Mock()
        mock_response.text = "Great progress on your recent tasks! Your consistent morning productivity shows you're in your optimal zone. Next step: tackle that payment flow design - break it into 30-minute focused sessions to maintain momentum."
        mock_ai_service.model.generate_content.return_value = mock_response

        message = await mock_ai_service.generate_motivation_message(
            user=sample_user,
            ai_context=sample_ai_context,
            current_challenge="Feeling overwhelmed with MVP scope",
            stress_level=6,
            recent_completions=sample_tasks
        )

        assert "Great progress" in message
        assert "Next step" in message
        mock_ai_service.model.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_motivation_message_ai_failure(self, mock_ai_service, sample_user, sample_ai_context, sample_tasks):
        """Test motivation message generation when AI fails."""
        mock_ai_service.model.generate_content.side_effect = Exception("AI service error")

        message = await mock_ai_service.generate_motivation_message(
            user=sample_user,
            ai_context=sample_ai_context,
            current_challenge="Test challenge",
            stress_level=5,
            recent_completions=sample_tasks
        )

        # Should return fallback message
        assert "You're making progress on your entrepreneurial journey" in message
        assert sample_user.name in message


class TestDeadlineReminders:
    """Test deadline reminder generation (Agent 3)."""

    @pytest.mark.asyncio
    async def test_generate_deadline_reminder_success(self, mock_ai_service, sample_tasks):
        """Test successful deadline reminder generation."""
        mock_response = Mock()
        mock_response.text = "⏰ Authentication task due in 2 days! Given your consistent work pattern, block 2 hours tomorrow morning (your peak time) to complete this. Break it down: 1) API design, 2) Implementation, 3) Testing."
        mock_ai_service.model.generate_content.return_value = mock_response

        task = sample_tasks[0]
        task.deadline = datetime.now() + timedelta(days=2)

        reminder = await mock_ai_service.generate_deadline_reminder(
            task=task,
            time_remaining="2 days",
            user_pattern="Consistent",
            stress_level=4,
            completion_rate=85.0
        )

        assert "Authentication task" in reminder
        assert "2 days" in reminder
        mock_ai_service.model.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_deadline_reminder_ai_failure(self, mock_ai_service, sample_tasks):
        """Test deadline reminder generation when AI fails."""
        mock_ai_service.model.generate_content.side_effect = Exception("AI service error")

        task = sample_tasks[0]

        reminder = await mock_ai_service.generate_deadline_reminder(
            task=task,
            time_remaining="1 day",
            user_pattern="Procrastinator",
            stress_level=7,
            completion_rate=60.0
        )

        # Should return fallback reminder
        assert "Friendly reminder:" in reminder
        assert task.description in reminder
        assert "1 day remaining" in reminder


class TestWeeklyAnalysis:
    """Test weekly analysis generation (Agent 4)."""

    @pytest.mark.asyncio
    async def test_generate_weekly_analysis_success(self, mock_ai_service, sample_progress_logs, sample_goals, sample_tasks):
        """Test successful weekly analysis generation."""
        mock_response = Mock()
        mock_response.text = '''```json
        {
            "insights": ["Strong morning productivity pattern", "Consistent task completion rate"],
            "bottlenecks": ["Friday energy drops", "Complex tasks taking longer"],
            "recommendations": ["Schedule complex tasks for Monday-Wednesday", "Add energy breaks on Friday", "Break large tasks into smaller chunks"],
            "motivation": "You've maintained 75% completion rate this week - excellent consistency! Your morning energy optimization is paying off.",
            "risks": ["Energy decline pattern on Fridays needs attention"]
        }
        ```'''
        mock_ai_service.model.generate_content.return_value = mock_response

        analysis = await mock_ai_service.generate_weekly_analysis(
            progress_logs=sample_progress_logs,
            goals=sample_goals,
            tasks=sample_tasks
        )

        assert "insights" in analysis
        assert "bottlenecks" in analysis
        assert "recommendations" in analysis
        assert "motivation" in analysis
        assert "risks" in analysis
        assert len(analysis["recommendations"]) == 3
        assert "morning productivity" in analysis["insights"][0]

    @pytest.mark.asyncio
    async def test_generate_weekly_analysis_ai_failure(self, mock_ai_service, sample_progress_logs, sample_goals, sample_tasks):
        """Test weekly analysis generation when AI fails."""
        mock_ai_service.model.generate_content.side_effect = Exception("AI service error")

        analysis = await mock_ai_service.generate_weekly_analysis(
            progress_logs=sample_progress_logs,
            goals=sample_goals,
            tasks=sample_tasks
        )

        # Should return fallback analysis
        assert "key_insights" in analysis
        assert "overall_performance" in analysis
        assert "productivity_score" in analysis
        assert analysis["overall_performance"] == "Good"


class TestPhaseTransitionEvaluation:
    """Test phase transition evaluation (Agent 5)."""

    @pytest.mark.asyncio
    async def test_evaluate_phase_transition_success(self, mock_ai_service, sample_user, sample_goals):
        """Test successful phase transition evaluation."""
        mock_response = Mock()
        mock_response.text = '''```json
        {
            "recommendation": "Go",
            "confidence_score": 85,
            "gaps": ["User onboarding flow incomplete", "Payment integration pending"],
            "improvements": ["Complete user testing", "Finalize payment system"],
            "success_probability": 80,
            "strategies": ["Focus on critical path items", "Parallel development streams"]
        }
        ```'''
        mock_ai_service.model.generate_content.return_value = mock_response

        # Mark one goal as completed
        sample_goals[0].status = StatusEnum.COMPLETED

        evaluation = await mock_ai_service.evaluate_phase_transition(
            user=sample_user,
            goals=sample_goals,
            time_in_phase_days=45
        )

        assert evaluation["recommendation"] == "Go"
        assert evaluation["confidence_score"] == 85
        assert len(evaluation["gaps"]) == 2
        assert evaluation["success_probability"] == 80

    @pytest.mark.asyncio
    async def test_evaluate_phase_transition_no_go(self, mock_ai_service, sample_user, sample_goals):
        """Test phase transition evaluation with No-Go recommendation."""
        mock_response = Mock()
        mock_response.text = '''```json
        {
            "recommendation": "No-Go",
            "confidence_score": 75,
            "gaps": ["Only 25% goals completed", "Key features missing"],
            "improvements": ["Complete MVP core features", "Achieve 70% goal completion"],
            "success_probability": 40,
            "strategies": ["Extend MVP phase by 30 days", "Focus on essential features only"]
        }
        ```'''
        mock_ai_service.model.generate_content.return_value = mock_response

        evaluation = await mock_ai_service.evaluate_phase_transition(
            user=sample_user,
            goals=sample_goals,
            time_in_phase_days=30
        )

        assert evaluation["recommendation"] == "No-Go"
        assert evaluation["success_probability"] == 40


class TestCareerTransitionAnalysis:
    """Test career transition analysis (Agent 6)."""

    @pytest.mark.asyncio
    async def test_analyze_career_transition_readiness_success(self, mock_ai_service, sample_user, sample_job_metrics):
        """Test successful career transition analysis."""
        mock_response = Mock()
        mock_response.text = '''```json
        {
            "risk_level": "Medium",
            "optimal_timing": "6-8 months",
            "milestones": ["Reach $2500 monthly revenue", "Build 12-month runway", "Secure first enterprise client"],
            "financial_safety": ["Emergency fund of 6 months expenses", "Revenue growth trajectory of 20% monthly"],
            "recommendation": "You're on the right track with 30% salary replacement. Focus on customer acquisition and revenue growth. Consider part-time transition when you hit 50% salary replacement."
        }
        ```'''
        mock_ai_service.model.generate_content.return_value = mock_response

        analysis = await mock_ai_service.analyze_career_transition_readiness(
            user=sample_user,
            job_metrics=sample_job_metrics
        )

        assert analysis["risk_level"] == "Medium"
        assert analysis["optimal_timing"] == "6-8 months"
        assert len(analysis["milestones"]) == 3
        assert "salary replacement" in analysis["recommendation"]

    @pytest.mark.asyncio
    async def test_analyze_career_transition_high_risk(self, mock_ai_service, sample_user):
        """Test career transition analysis with high risk scenario."""
        # Create high-risk job metrics
        high_risk_metrics = JobMetrics(
            user_id=sample_user.telegram_id,
            current_salary=Decimal("6000.00"),
            startup_revenue=Decimal("200.00"),  # Very low revenue
            monthly_expenses=Decimal("4500.00"),
            runway_months=2.0,  # Very low runway
            stress_level=9,
            job_satisfaction=2
        )

        mock_response = Mock()
        mock_response.text = '''```json
        {
            "risk_level": "High",
            "optimal_timing": "12+ months",
            "milestones": ["Increase revenue to $3000/month", "Build 12-month runway", "Reduce monthly expenses"],
            "financial_safety": ["Emergency fund", "Stable client base", "Multiple revenue streams"],
            "recommendation": "Current financial position is too risky for transition. Focus on revenue growth and expense reduction before considering career change."
        }
        ```'''
        mock_ai_service.model.generate_content.return_value = mock_response

        analysis = await mock_ai_service.analyze_career_transition_readiness(
            user=sample_user,
            job_metrics=high_risk_metrics
        )

        assert analysis["risk_level"] == "High"
        assert "12+" in analysis["optimal_timing"]
        assert "too risky" in analysis["recommendation"]

    @pytest.mark.asyncio
    async def test_ai_service_initialization_without_api_key(self):
        """Test AI service initialization fails without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable is required"):
                AIService()

    @pytest.mark.asyncio
    async def test_ai_service_initialization_with_api_key(self):
        """Test AI service initialization succeeds with API key."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            with patch('google.generativeai.configure') as mock_configure:
                with patch('google.generativeai.GenerativeModel') as mock_model:
                    service = AIService()
                    mock_configure.assert_called_once_with(api_key='test-key')
                    mock_model.assert_called_once_with('gemini-2.5-flash')


class TestGoalsAnalysis:
    """Test goals analysis generation (Agent 7)."""

    @pytest.mark.asyncio
    async def test_analyze_goals_success(self, mock_ai_service, sample_goals, sample_progress_logs):
        """Test successful goals analysis generation."""
        mock_response = Mock()
        mock_response.text = '''```json
        {
            "overall_status": "Good",
            "completion_assessment": "On Track",
            "key_insights": [
                "Strong progress on MVP goals",
                "Consistent goal completion rate",
                "Good priority balance"
            ],
            "success_patterns": [
                "Regular progress tracking",
                "Focus on high-priority items"
            ],
            "challenges": [
                "Some goals need more detailed milestones",
                "Long-term goals need more attention"
            ],
            "recommendations": [
                "Break down complex goals into smaller tasks",
                "Set clear weekly milestones",
                "Review and adjust priorities monthly"
            ],
            "priority_adjustments": [
                "Increase focus on user acquisition goals",
                "Balance technical and business objectives"
            ],
            "achievement_score": 75,
            "focus_areas": [
                "User growth metrics",
                "Technical infrastructure"
            ]
        }
        ```'''
        mock_ai_service.model.generate_content.return_value = mock_response

        # Mark one goal as completed for testing
        sample_goals[0].status = StatusEnum.COMPLETED
        sample_goals[1].status = StatusEnum.ACTIVE
        sample_goals[1].completion_percentage = 60

        analysis = await mock_ai_service.analyze_goals(
            goals=sample_goals,
            progress_logs=sample_progress_logs
        )

        assert analysis["overall_status"] == "Good"
        assert analysis["completion_assessment"] == "On Track"
        assert len(analysis["key_insights"]) == 3
        assert len(analysis["success_patterns"]) == 2
        assert len(analysis["challenges"]) == 2
        assert len(analysis["recommendations"]) == 3
        assert len(analysis["priority_adjustments"]) == 2
        assert analysis["achievement_score"] == 75
        assert len(analysis["focus_areas"]) == 2

        # Verify the call was made with correct prompt context
        mock_ai_service.model.generate_content.assert_called_once()
        call_args = mock_ai_service.model.generate_content.call_args[0][0]
        assert "Goal Metrics:" in call_args
        assert "Total Goals: 2" in call_args
        assert "Completed: 1" in call_args
        assert "In Progress: 1" in call_args

    @pytest.mark.asyncio
    async def test_analyze_goals_no_progress_logs(self, mock_ai_service, sample_goals):
        """Test goals analysis without progress logs."""
        mock_response = Mock()
        mock_response.text = '''```json
        {
            "overall_status": "Average",
            "completion_assessment": "On Track",
            "key_insights": ["Regular goal setting maintained"],
            "success_patterns": ["Consistent tracking"],
            "challenges": ["Need more progress data"],
            "recommendations": ["Start tracking daily progress"],
            "priority_adjustments": ["Review goal priorities"],
            "achievement_score": 65,
            "focus_areas": ["Progress tracking", "Goal completion"]
        }
        ```'''
        mock_ai_service.model.generate_content.return_value = mock_response

        analysis = await mock_ai_service.analyze_goals(goals=sample_goals)

        assert analysis["overall_status"] == "Average"
        assert "progress data" in analysis["challenges"][0]
        mock_ai_service.model.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_goals_ai_failure(self, mock_ai_service, sample_goals):
        """Test goals analysis when AI fails."""
        mock_ai_service.model.generate_content.side_effect = Exception("AI service error")

        analysis = await mock_ai_service.analyze_goals(goals=sample_goals)

        # Should return fallback analysis
        assert "overall_status" in analysis
        assert "completion_assessment" in analysis
        assert "key_insights" in analysis
        assert "recommendations" in analysis
        assert isinstance(analysis["achievement_score"], int)
        assert analysis["achievement_score"] >= 0
        assert analysis["achievement_score"] <= 100


class TestAIServiceIntegration:
    """Integration tests for AI Service with realistic scenarios."""

    @pytest.mark.asyncio
    async def test_complete_daily_workflow(self, mock_ai_service, sample_user, sample_progress_logs, sample_goals, sample_ai_context, sample_tasks):
        """Test complete daily AI workflow."""
        # Mock all AI responses
        daily_tasks_response = Mock()
        daily_tasks_response.text = '''[{"description": "Work on MVP features", "estimated_duration": 120, "energy_required": "High", "priority": "High"}]'''
        
        motivation_response = Mock()
        motivation_response.text = "You're making great progress! Focus on one task at a time."
        
        reminder_response = Mock()
        reminder_response.text = "Don't forget your important task due soon!"

        mock_ai_service.model.generate_content.side_effect = [
            daily_tasks_response,
            motivation_response,
            reminder_response
        ]

        # Test daily task generation
        tasks = await mock_ai_service.generate_daily_tasks(
            user=sample_user,
            recent_progress=sample_progress_logs,
            pending_goals=sample_goals,
            today_energy_level=7
        )

        # Test motivation message
        motivation = await mock_ai_service.generate_motivation_message(
            user=sample_user,
            ai_context=sample_ai_context,
            current_challenge="Scope creep",
            stress_level=5,
            recent_completions=sample_tasks
        )

        # Test deadline reminder
        task_with_deadline = sample_tasks[0]
        task_with_deadline.deadline = datetime.now() + timedelta(hours=24)
        
        reminder = await mock_ai_service.generate_deadline_reminder(
            task=task_with_deadline,
            time_remaining="1 day",
            user_pattern="Consistent",
            stress_level=4,
            completion_rate=80.0
        )

        assert len(tasks) == 1
        assert "MVP features" in tasks[0]["description"]
        assert "great progress" in motivation
        assert "Don't forget" in reminder
        
        # Verify all AI calls were made
        assert mock_ai_service.model.generate_content.call_count == 3 