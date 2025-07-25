import pytest
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.user import User, PhaseEnum, EnergyProfileEnum, TimezoneEnum
from app.models.goal import Goal, GoalTypeEnum, StatusEnum, PriorityEnum
from app.models.task import Task, TaskPriorityEnum, CompletionStatusEnum, EnergyRequiredEnum
from app.models.progress_log import ProgressLog
from app.models.ai_context import AIContext
from app.models.job_metrics import JobMetrics
from app.services.ai_service import AIService


class TestAISystemIntegration:
    """Integration tests for the complete AI-powered productivity system."""

    @pytest.fixture
    def complete_user_setup(self, session: Session):
        """Set up a complete user with all related data."""
        # Create user
        user = User(
            telegram_id="987654321",
            name="Jane Startup",
            birthday=date(1985, 8, 20),
            timezone=TimezoneEnum.PST,
            current_phase=PhaseEnum.GROWTH,
            quit_job_target=date(2024, 10, 1),
            onboarding_complete=True,
            morning_time=datetime.strptime("06:30", "%H:%M").time(),
            energy_profile=EnergyProfileEnum.MORNING
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create goals
        goals = [
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Scale product to 10,000 users",
                deadline=date(2024, 6, 30),
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.GROWTH,
                priority=PriorityEnum.HIGH,
                completion_percentage=65.0
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.MONTHLY,
                description="Implement advanced analytics",
                deadline=date(2024, 4, 15),
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.GROWTH,
                priority=PriorityEnum.MEDIUM,
                completion_percentage=40.0
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.WEEKLY,
                description="Optimize conversion funnel",
                deadline=date(2024, 3, 10),
                status=StatusEnum.COMPLETED,
                phase=PhaseEnum.GROWTH,
                priority=PriorityEnum.HIGH,
                completion_percentage=100.0
            )
        ]
        for goal in goals:
            session.add(goal)
        session.commit()

        # Create tasks
        tasks = [
            Task(
                user_id=user.telegram_id,
                goal_id=goals[0].goal_id,
                description="Implement user onboarding flow",
                deadline=datetime(2024, 3, 20, 16, 0),
                priority=TaskPriorityEnum.HIGH,
                ai_generated=True,
                completion_status=CompletionStatusEnum.COMPLETED,
                estimated_duration=180,
                actual_duration=165,
                energy_required=EnergyRequiredEnum.HIGH
            ),
            Task(
                user_id=user.telegram_id,
                goal_id=goals[1].goal_id,
                description="Set up A/B testing framework",
                deadline=datetime(2024, 3, 25, 18, 0),
                priority=TaskPriorityEnum.MEDIUM,
                ai_generated=True,
                completion_status=CompletionStatusEnum.IN_PROGRESS,
                estimated_duration=240,
                actual_duration=None,
                energy_required=EnergyRequiredEnum.MEDIUM
            ),
            Task(
                user_id=user.telegram_id,
                goal_id=goals[0].goal_id,
                description="Optimize database queries for scale",
                deadline=datetime(2024, 3, 30, 14, 0),
                priority=TaskPriorityEnum.URGENT,
                ai_generated=False,
                completion_status=CompletionStatusEnum.PENDING,
                estimated_duration=300,
                actual_duration=None,
                energy_required=EnergyRequiredEnum.HIGH
            )
        ]
        for task in tasks:
            session.add(task)
        session.commit()

        # Create progress logs
        progress_logs = []
        for i in range(14):  # Two weeks of data
            log = ProgressLog(
                user_id=user.telegram_id,
                date=date.today() - timedelta(days=i),
                tasks_completed=2 + (i % 3),  # Varying completion
                tasks_planned=4 + (i % 2),
                mood_score=6 + (i % 4),  # Mood varies 6-9
                energy_level=7 + (i % 3),  # Energy varies 7-9
                focus_score=5 + (i % 5),  # Focus varies 5-9
                daily_reflection=f"Day {i}: Working on growth phase objectives",
                ai_insights=f"Productivity pattern analysis for day {i}"
            )
            progress_logs.append(log)
            session.add(log)
        session.commit()

        # Create AI context
        ai_context = AIContext(
            user_id=user.telegram_id,
            behavior_patterns=json.dumps({
                "type": "consistent_performer",
                "peak_hours": ["06:30", "08:30", "14:00", "16:00"],
                "productivity_style": "deep_work_blocks",
                "completion_pattern": "strong_finisher",
                "stress_response": "maintains_quality"
            }),
            productivity_insights="Peak performance in early morning and mid-afternoon. Prefers 2-3 hour deep work blocks. Shows consistent completion rates with high quality output.",
            motivation_triggers="Progress milestones, user feedback, technical challenges, team collaboration",
            stress_indicators="Scattered focus when overcommitted, reduced creativity under tight deadlines, perfectionism delays",
            optimal_work_times="06:30-08:30 (deep work), 09:00-11:00 (meetings), 14:00-16:00 (implementation), 16:30-17:30 (admin)",
            last_updated=datetime.utcnow()
        )
        session.add(ai_context)
        session.commit()

        # Create job metrics
        job_metrics = JobMetrics(
            user_id=user.telegram_id,
            current_salary=Decimal("8500.00"),
            startup_revenue=Decimal("4200.00"),  # 50% salary replacement
            monthly_expenses=Decimal("5200.00"),
            runway_months=12.5,
            stress_level=5,  # Moderate stress
            job_satisfaction=3,  # Low satisfaction, ready to leave
            quit_readiness_score=85.0,  # High readiness
            last_updated=datetime.utcnow()
        )
        session.add(job_metrics)
        session.commit()

        return {
            "user": user,
            "goals": goals,
            "tasks": tasks,
            "progress_logs": progress_logs,
            "ai_context": ai_context,
            "job_metrics": job_metrics
        }

    @pytest.fixture
    def mock_ai_service_responses(self):
        """Mock all AI service responses for integration testing."""
        return {
            "daily_tasks": '''```json
            [
                {
                    "description": "Optimize database connection pooling for 10K+ concurrent users",
                    "estimated_duration": 180,
                    "energy_required": "High",
                    "priority": "Urgent"
                },
                {
                    "description": "Implement Redis caching for frequently accessed data",
                    "estimated_duration": 120,
                    "energy_required": "Medium", 
                    "priority": "High"
                },
                {
                    "description": "Review and document scaling architecture decisions",
                    "estimated_duration": 90,
                    "energy_required": "Low",
                    "priority": "Medium"
                }
            ]
            ```''',
            
            "motivation": "Fantastic progress on your growth phase! You're at 50% salary replacement - exactly where you need to be for a confident transition. Your consistent morning productivity and deep work blocks are paying off. Today's focus: nail that database optimization to handle your growing user base. You're so close to your freedom date!",
            
            "deadline_reminder": "🚨 Database optimization due in 5 days! Your consistent performer profile suggests blocking 3 hours tomorrow morning (6:30-9:30 AM) for this. Break it down: 1) Connection pooling (90min), 2) Query optimization (60min), 3) Performance testing (30min). You've got this! 💪",
            
            "weekly_analysis": '''```json
            {
                "insights": [
                    "Maintained 78% task completion rate despite increased complexity",
                    "Deep work blocks (2-3 hours) show 40% higher efficiency than scattered work",
                    "Morning productivity peak consistently outperforms afternoon by 25%",
                    "Quality maintenance under pressure - zero critical bugs this week"
                ],
                "bottlenecks": [
                    "Context switching during 9-11 AM meeting slots reduces focus",
                    "Perfectionism causing 15% timeline extension on complex tasks",
                    "Administrative tasks accumulating in late afternoon"
                ],
                "recommendations": [
                    "Batch meetings into single 2-hour block (9-11 AM) to preserve deep work time",
                    "Set 'good enough' checkpoints for perfectionism-prone tasks",
                    "Delegate or automate recurring admin tasks to focus on high-impact work",
                    "Schedule database optimization for 6:30-9:30 AM deep work block"
                ],
                "motivation": "You're absolutely crushing the growth phase! 85% quit readiness score with 50% salary replacement puts you in the driver's seat. Your technical leadership is building something amazing - stay focused on the big picture.",
                "risks": [
                    "Approaching technical debt threshold - allocate 20% time for refactoring",
                    "Meeting overload could impact core development time"
                ]
            }
            ```''',
            
            "phase_transition": '''```json
            {
                "recommendation": "Go",
                "confidence_score": 88,
                "gaps": [
                    "Advanced analytics implementation at 40% - needs completion",
                    "Monitoring and alerting system for scale operations"
                ],
                "improvements": [
                    "Complete analytics dashboard by April 15th",
                    "Implement comprehensive monitoring before scaling further",
                    "Document scaling procedures for team onboarding"
                ],
                "success_probability": 85,
                "strategies": [
                    "Parallel track: analytics completion while scaling infrastructure",
                    "Bring in DevOps expertise for monitoring systems",
                    "Incremental scaling approach to validate architecture decisions"
                ]
            }
            ```''',
            
            "career_transition": '''```json
            {
                "risk_level": "Low",
                "optimal_timing": "2-3 months",
                "milestones": [
                    "Maintain $4200+ monthly revenue for 3 consecutive months",
                    "Complete growth phase objectives (analytics + monitoring)",
                    "Build team to handle day-to-day operations",
                    "Secure 6-month contract or enterprise client for stability"
                ],
                "financial_safety": [
                    "12.5-month runway provides excellent buffer",
                    "Revenue at 50% salary replacement - ideal transition point",
                    "Emergency fund recommendation: maintain current runway",
                    "Revenue diversification: reduce single client dependency"
                ],
                "recommendation": "You're in an excellent position for career transition. 50% salary replacement with 12+ month runway is the sweet spot most advisors recommend. Your growth phase completion should coincide perfectly with your October transition target. Consider negotiating part-time arrangement with current employer as backup plan. The technical foundation you're building is solid - focus on business operations and team building now."
            }
            ```'''
        }

    @pytest.mark.asyncio
    async def test_complete_ai_workflow_integration(self, complete_user_setup, mock_ai_service_responses):
        """Test the complete AI workflow integration with realistic data."""
        
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-api-key'}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_model:
                    # Setup AI service with mocked responses
                    mock_instance = Mock()
                    mock_model.return_value = mock_instance
                    
                    # Configure mock responses in order of expected calls
                    mock_responses = [
                        Mock(text=mock_ai_service_responses["daily_tasks"]),
                        Mock(text=mock_ai_service_responses["motivation"]),
                        Mock(text=mock_ai_service_responses["deadline_reminder"]),
                        Mock(text=mock_ai_service_responses["weekly_analysis"]),
                        Mock(text=mock_ai_service_responses["phase_transition"]),
                        Mock(text=mock_ai_service_responses["career_transition"])
                    ]
                    mock_instance.generate_content.side_effect = mock_responses
                    
                    ai_service = AIService()
                    ai_service.model = mock_instance
                    
                    data = complete_user_setup
                    user = data["user"]
                    goals = data["goals"]
                    tasks = data["tasks"]
                    progress_logs = data["progress_logs"]
                    ai_context = data["ai_context"]
                    job_metrics = data["job_metrics"]

                    # Test 1: Daily Task Generation (Agent 1)
                    daily_tasks = await ai_service.generate_daily_tasks(
                        user=user,
                        recent_progress=progress_logs[-7:],  # Last 7 days
                        pending_goals=[g for g in goals if g.status == StatusEnum.ACTIVE],
                        today_energy_level=8
                    )
                    
                    assert len(daily_tasks) == 3
                    assert "database connection pooling" in daily_tasks[0]["description"].lower()
                    assert daily_tasks[0]["priority"] == "Urgent"
                    assert daily_tasks[0]["estimated_duration"] == 180
                    
                    # Test 2: Motivation Message (Agent 2)
                    motivation = await ai_service.generate_motivation_message(
                        user=user,
                        ai_context=ai_context,
                        current_challenge="Scaling database performance for growing user base",
                        stress_level=5,
                        recent_completions=[t for t in tasks if t.completion_status == CompletionStatusEnum.COMPLETED]
                    )
                    
                    assert "50% salary replacement" in motivation
                    assert "growth phase" in motivation.lower()
                    assert "freedom date" in motivation.lower()

                    # Test 3: Deadline Reminder (Agent 3)
                    urgent_task = next(t for t in tasks if t.priority == TaskPriorityEnum.URGENT)
                    reminder = await ai_service.generate_deadline_reminder(
                        task=urgent_task,
                        time_remaining="5 days",
                        user_pattern="consistent_performer",
                        stress_level=5,
                        completion_rate=78.0
                    )
                    
                    assert "database optimization" in reminder.lower()
                    assert "5 days" in reminder
                    assert "6:30-9:30" in reminder  # User's optimal morning time

                    # Test 4: Weekly Analysis (Agent 4)
                    weekly_analysis = await ai_service.generate_weekly_analysis(
                        progress_logs=progress_logs[-7:],
                        goals=goals,
                        tasks=tasks
                    )
                    
                    assert "insights" in weekly_analysis
                    assert "bottlenecks" in weekly_analysis
                    assert "recommendations" in weekly_analysis
                    assert len(weekly_analysis["recommendations"]) == 4
                    assert "78% task completion" in weekly_analysis["insights"][0]

                    # Test 5: Phase Transition Evaluation (Agent 5)
                    phase_eval = await ai_service.evaluate_phase_transition(
                        user=user,
                        goals=goals,
                        time_in_phase_days=90  # 3 months in growth phase
                    )
                    
                    assert phase_eval["recommendation"] == "Go"
                    assert phase_eval["confidence_score"] == 88
                    assert phase_eval["success_probability"] == 85
                    assert "analytics implementation" in phase_eval["gaps"][0].lower()

                    # Test 6: Career Transition Analysis (Agent 6)
                    career_analysis = await ai_service.analyze_career_transition_readiness(
                        user=user,
                        job_metrics=job_metrics
                    )
                    
                    assert career_analysis["risk_level"] == "Low"
                    assert "2-3 months" in career_analysis["optimal_timing"]
                    assert "50% salary replacement" in career_analysis["recommendation"]
                    assert len(career_analysis["milestones"]) == 4

                    # Verify all AI agents were called
                    assert mock_instance.generate_content.call_count == 6

    @pytest.mark.asyncio
    async def test_ai_workflow_with_different_user_profiles(self, session: Session):
        """Test AI workflow with different user profiles and phases."""
        
        # Test Profile 1: Research Phase, Low Progress
        research_user = User(
            telegram_id="research123",
            name="Research Bob",
            current_phase=PhaseEnum.RESEARCH,
            energy_profile=EnergyProfileEnum.EVENING,
            onboarding_complete=False
        )
        session.add(research_user)
        
        research_goal = Goal(
            user_id=research_user.telegram_id,
            type=GoalTypeEnum.MONTHLY,
            description="Validate business idea",
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.HIGH,
            completion_percentage=15.0
        )
        session.add(research_goal)
        session.commit()

        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-api-key'}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_model:
                    mock_instance = Mock()
                    mock_model.return_value = mock_instance
                    
                    # Mock fallback responses for research phase
                    mock_instance.generate_content.return_value = Mock(
                        text='[{"description": "Work on Research phase objectives for 1 hour", "estimated_duration": 60, "energy_required": "Medium", "priority": "High"}]'
                    )
                    
                    ai_service = AIService()
                    ai_service.model = mock_instance
                    
                    daily_tasks = await ai_service.generate_daily_tasks(
                        user=research_user,
                        recent_progress=[],
                        pending_goals=[research_goal],
                        today_energy_level=4
                    )
                    
                    assert len(daily_tasks) == 1
                    assert "Research phase" in daily_tasks[0]["description"]

    @pytest.mark.asyncio
    async def test_ai_error_handling_and_fallbacks(self, complete_user_setup):
        """Test AI service error handling and fallback mechanisms."""
        
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-api-key'}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_model:
                    mock_instance = Mock()
                    mock_model.return_value = mock_instance
                    
                    # Simulate AI service failures
                    mock_instance.generate_content.side_effect = Exception("API Rate Limit Exceeded")
                    
                    ai_service = AIService()
                    ai_service.model = mock_instance
                    
                    data = complete_user_setup
                    user = data["user"]
                    goals = data["goals"]
                    progress_logs = data["progress_logs"]
                    ai_context = data["ai_context"]
                    job_metrics = data["job_metrics"]

                    # Test fallback for daily tasks
                    daily_tasks = await ai_service.generate_daily_tasks(
                        user=user,
                        recent_progress=progress_logs[-7:],
                        pending_goals=goals,
                        today_energy_level=7
                    )
                    
                    assert len(daily_tasks) == 2  # Updated to expect 2 fallback tasks
                    assert "Review and prioritize today's goals" in daily_tasks[0]["description"]

                    # Test fallback for motivation
                    motivation = await ai_service.generate_motivation_message(
                        user=user,
                        ai_context=ai_context,
                        current_challenge="API issues",
                        stress_level=6,
                        recent_completions=[]
                    )
                    
                    assert "You're making progress on your entrepreneurial journey" in motivation
                    assert user.name in motivation  # User name should be included in fallback

                    # Test fallback for career analysis
                    career_analysis = await ai_service.analyze_career_transition_readiness(
                        user=user,
                        job_metrics=job_metrics
                    )
                    
                    # Should return reasonable fallback based on metrics
                    assert career_analysis["risk_level"] in ["High", "Medium", "Low"]
                    assert "months" in career_analysis["timeline_recommendation"]

    @pytest.mark.asyncio 
    async def test_ai_context_learning_and_adaptation(self, complete_user_setup):
        """Test how AI adapts recommendations based on user context and history."""
        
        data = complete_user_setup
        user = data["user"]
        ai_context = data["ai_context"]
        progress_logs = data["progress_logs"]
        
        # Parse the behavior patterns to test adaptation
        behavior_data = json.loads(ai_context.behavior_patterns)
        
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-api-key'}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_model:
                    mock_instance = Mock()
                    mock_model.return_value = mock_instance
                    
                    # Mock context-aware response
                    context_aware_response = Mock()
                    context_aware_response.text = f"Based on your consistent_performer profile and peak hours at {behavior_data['peak_hours']}, I recommend starting with your highest energy task during your 06:30-08:30 deep work block. Your strong_finisher pattern suggests you'll maintain quality even under pressure."
                    
                    mock_instance.generate_content.return_value = context_aware_response
                    
                    ai_service = AIService()
                    ai_service.model = mock_instance
                    
                    motivation = await ai_service.generate_motivation_message(
                        user=user,
                        ai_context=ai_context,
                        current_challenge="Managing technical complexity",
                        stress_level=4,
                        recent_completions=[]
                    )
                    
                    # Verify AI used context data
                    assert "consistent_performer" in motivation
                    assert "06:30-08:30" in motivation
                    assert "deep work block" in motivation
                    
                    # Verify the prompt included motivation triggers
                    call_args = mock_instance.generate_content.call_args[0][0]
                    assert ai_context.motivation_triggers in call_args

    def test_integration_with_database_relationships(self, complete_user_setup, session: Session):
        """Test that all database relationships work correctly in integration."""
        
        data = complete_user_setup
        user = data["user"]
        
        # Test user relationships are properly loaded
        session.refresh(user)
        
        assert len(user.goals) == 3
        assert len(user.tasks) == 3
        assert len(user.progress_logs) == 14
        assert user.ai_context is not None
        assert user.job_metrics is not None
        
        # Test goal-task relationships
        for goal in user.goals:
            session.refresh(goal)
            if goal.status == StatusEnum.ACTIVE:
                assert len([t for t in user.tasks if t.goal_id == goal.goal_id]) > 0
        
        # Test data consistency
        completed_goals = [g for g in user.goals if g.status == StatusEnum.COMPLETED]
        assert len(completed_goals) == 1
        assert completed_goals[0].completion_percentage == 100.0
        
        # Test AI context contains valid JSON
        behavior_patterns = json.loads(user.ai_context.behavior_patterns)
        assert "type" in behavior_patterns
        assert "peak_hours" in behavior_patterns
        assert isinstance(behavior_patterns["peak_hours"], list)

    @pytest.mark.asyncio
    async def test_performance_under_load(self, complete_user_setup):
        """Test AI service performance with realistic data volumes."""
        
        data = complete_user_setup
        user = data["user"]
        
        # Simulate large dataset
        large_progress_logs = []
        for i in range(365):  # Full year of data
            log = ProgressLog(
                user_id=user.telegram_id,
                date=date.today() - timedelta(days=i),
                tasks_completed=2 + (i % 4),
                tasks_planned=5,
                mood_score=5 + (i % 5),
                energy_level=6 + (i % 4),
                focus_score=4 + (i % 6)
            )
            large_progress_logs.append(log)
        
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-api-key'}):
            with patch('google.generativeai.configure'):
                with patch('google.generativeai.GenerativeModel') as mock_model:
                    mock_instance = Mock()
                    mock_model.return_value = mock_instance
                    mock_instance.generate_content.return_value = Mock(
                        text='{"insights": ["Performance analysis complete"], "recommendations": ["Continue current approach"]}'
                    )
                    
                    ai_service = AIService()
                    ai_service.model = mock_instance
                    
                    # Test that AI service can handle large datasets efficiently
                    start_time = datetime.now()
                    
                    analysis = await ai_service.generate_weekly_analysis(
                        progress_logs=large_progress_logs[:30],  # Last 30 days
                        goals=data["goals"],
                        tasks=data["tasks"]
                    )
                    
                    end_time = datetime.now()
                    processing_time = (end_time - start_time).total_seconds()
                    
                    # Should complete within reasonable time (< 5 seconds for processing)
                    assert processing_time < 5.0
                    assert "insights" in analysis
                    
                    # Verify large dataset was processed correctly
                    call_args = mock_instance.generate_content.call_args[0][0]
                    assert "Metrics:" in call_args 