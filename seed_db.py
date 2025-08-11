from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal
from sqlmodel import Session, SQLModel, create_engine, select
import os
from app.core.config import settings

# Use database URL from settings
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {})

def create_db_and_tables():
    """Create database and all tables."""
    SQLModel.metadata.create_all(engine)

from app.models.user import User, TimezoneEnum, PhaseEnum, EnergyProfileEnum
from app.models.goal import Goal, GoalTypeEnum, StatusEnum, PriorityEnum
from app.models.task import Task, TaskPriorityEnum, CompletionStatusEnum, EnergyRequiredEnum
from app.models.job_metrics import JobMetrics
from app.models.progress_log import ProgressLog
from app.models.day_log import DayLog
from app.models.ai_context import AIContext

def cleanup_existing_data(session, telegram_id):
    """Remove existing data for the given telegram_id"""
    # Delete existing tasks
    tasks = session.exec(select(Task).where(Task.user_id == telegram_id)).all()
    for task in tasks:
        session.delete(task)
    
    # Delete existing progress logs
    progress_logs = session.exec(select(ProgressLog).where(ProgressLog.user_id == telegram_id)).all()
    for log in progress_logs:
        session.delete(log)
    
    # Delete existing day logs
    day_logs = session.exec(select(DayLog).where(DayLog.user_id == telegram_id)).all()
    for log in day_logs:
        session.delete(log)
    
    # Delete existing AI context
    ai_context = session.exec(select(AIContext).where(AIContext.user_id == telegram_id)).first()
    if ai_context:
        session.delete(ai_context)
    
    # Delete existing goals
    goals = session.exec(select(Goal).where(Goal.user_id == telegram_id)).all()
    for goal in goals:
        session.delete(goal)
    
    # Delete existing job metrics
    job_metrics = session.exec(select(JobMetrics).where(JobMetrics.user_id == telegram_id)).all()
    for metric in job_metrics:
        session.delete(metric)
    
    # Delete existing user
    user = session.exec(select(User).where(User.telegram_id == telegram_id)).first()
    if user:
        session.delete(user)
    
    session.commit()

def seed_database():
    # Create tables if they don't exist
    create_db_and_tables()
    
    with Session(engine) as session:
        telegram_id = "5976080378"
        
        # Clean up existing data
        cleanup_existing_data(session, telegram_id)
        
        # Create user
        user = User(
            telegram_id=telegram_id,
            name="Saif Husain Ansari",
            birthday=date(1995, 6, 15),  # Sample birthday
            timezone=TimezoneEnum.IST,
            current_phase=PhaseEnum.RESEARCH,
            energy_profile=EnergyProfileEnum.MORNING,
            quit_job_target=date(2025, 3, 1),  # Target to quit job
            morning_time=time(6, 0),  # 6 AM start time
            onboarding_complete=True
        )
        session.add(user)
        session.commit()

        # Create job metrics
        job_metrics = JobMetrics(
            user_id=user.telegram_id,
            current_salary=Decimal("1200000"),
            startup_revenue=Decimal("0"),
            monthly_expenses=Decimal("30000"),
            runway_months=12.0,
            stress_level=6,  # Moderate stress
            job_satisfaction=5,  # Neutral satisfaction
            quit_readiness_score=7.5,  # Pretty ready to quit
            last_updated=datetime.now(),  # IST
            ai_analysis={
                "career_growth_score": 3.5,
                "financial_health_score": 7.0,
                "work_life_balance_score": 4.0,
                "overall_recommendation": "Consider transitioning to entrepreneurship within 6-12 months",
                "action_items": [
                    "Build emergency fund to 6 months of expenses",
                    "Start networking in target industry",
                    "Begin side project validation"
                ],
                "risk_factors": [
                    "Limited startup experience",
                    "Current job provides stability"
                ],
                "opportunities": [
                    "Strong technical background",
                    "Growing market demand",
                    "Supportive network"
                ]
            }
        )
        session.add(job_metrics)
        session.commit()

        # Create main yearly goal
        main_goal = Goal(
            user_id=user.telegram_id,
            type=GoalTypeEnum.YEARLY,
            description="Build a successful startup within a year",
            deadline=date(2025, 5, 1),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.HIGH,
            completion_percentage=15.0
        )
        session.add(main_goal)

        # Create quarterly goals
        q1_goal = Goal(
            user_id=user.telegram_id,
            type=GoalTypeEnum.QUARTERLY,
            description="Complete market research and validate business idea",
            deadline=date(2024, 8, 1),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.HIGH,
            completion_percentage=60.0
        )
        session.add(q1_goal)

        q2_goal = Goal(
            user_id=user.telegram_id,
            type=GoalTypeEnum.QUARTERLY,
            description="Develop MVP and get initial user feedback",
            deadline=date(2024, 11, 1),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.MVP,
            priority=PriorityEnum.HIGH,
            completion_percentage=25.0
        )
        session.add(q2_goal)

        # Create monthly goals
        monthly_goal = Goal(
            user_id=user.telegram_id,
            type=GoalTypeEnum.MONTHLY,
            description="Complete competitor analysis and define unique value proposition",
            deadline=date(2024, 7, 31),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.MEDIUM,
            completion_percentage=80.0
        )
        session.add(monthly_goal)

        # Create weekly goals
        weekly_goal = Goal(
            user_id=user.telegram_id,
            type=GoalTypeEnum.WEEKLY,
            description="Interview 5 potential customers and document insights",
            deadline=date(2024, 7, 7),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.HIGH,
            completion_percentage=40.0
        )
        session.add(weekly_goal)

        session.commit()

        # Create tasks
        tasks = [
            Task(
                user_id=user.telegram_id,
                goal_id=q1_goal.goal_id,
                description="Research top 10 competitors in the target market",
                priority=TaskPriorityEnum.HIGH,
                completion_status=CompletionStatusEnum.COMPLETED,
                estimated_duration=120,
                actual_duration=90,
                energy_required=EnergyRequiredEnum.MEDIUM,
                scheduled_for_date=date(2024, 7, 1),
                started_at=datetime(2024, 7, 1, 9, 0),
                completed_at=datetime(2024, 7, 1, 10, 30),
                ai_generated=False
            ),
            Task(
                user_id=user.telegram_id,
                goal_id=q1_goal.goal_id,
                description="Create customer interview questions and schedule calls",
                priority=TaskPriorityEnum.HIGH,
                completion_status=CompletionStatusEnum.IN_PROGRESS,
                estimated_duration=60,
                actual_duration=45,
                energy_required=EnergyRequiredEnum.LOW,
                scheduled_for_date=date(2024, 7, 2),
                started_at=datetime(2024, 7, 2, 14, 0),
                ai_generated=True
            ),
            Task(
                user_id=user.telegram_id,
                goal_id=q2_goal.goal_id,
                description="Design initial wireframes for MVP",
                priority=TaskPriorityEnum.MEDIUM,
                completion_status=CompletionStatusEnum.PENDING,
                estimated_duration=180,
                energy_required=EnergyRequiredEnum.HIGH,
                scheduled_for_date=date(2024, 7, 5),
                ai_generated=True
            ),
            Task(
                user_id=user.telegram_id,
                goal_id=weekly_goal.goal_id,
                description="Conduct customer interview with John from TechCorp",
                priority=TaskPriorityEnum.URGENT,
                completion_status=CompletionStatusEnum.PENDING,
                estimated_duration=30,
                energy_required=EnergyRequiredEnum.MEDIUM,
                scheduled_for_date=date(2024, 7, 3),
                ai_generated=False
            ),
            Task(
                user_id=user.telegram_id,
                goal_id=monthly_goal.goal_id,
                description="Write competitive analysis report",
                priority=TaskPriorityEnum.MEDIUM,
                completion_status=CompletionStatusEnum.IN_PROGRESS,
                estimated_duration=240,
                actual_duration=120,
                energy_required=EnergyRequiredEnum.HIGH,
                scheduled_for_date=date(2024, 7, 4),
                started_at=datetime(2024, 7, 4, 8, 0),
                ai_generated=False
            )
        ]
        
        for task in tasks:
            session.add(task)
        session.commit()

        # Create progress logs for the last 7 days
        progress_logs = []
        for i in range(7):
            log_date = date.today() - timedelta(days=i)
            progress_logs.append(ProgressLog(
                user_id=user.telegram_id,
                date=log_date,
                tasks_completed=3 + (i % 3),  # Varying completion
                tasks_planned=5,
                mood_score=6 + (i % 3),  # Varying mood
                energy_level=7 + (i % 2),  # Varying energy
                focus_score=6 + (i % 3),  # Varying focus
                daily_reflection=f"Day {i+1}: Made good progress on market research. Need to improve time management.",
                ai_insights=f"AI Insight Day {i+1}: Your productivity peaks between 9-11 AM. Consider scheduling high-energy tasks during this window."
            ))
        
        for log in progress_logs:
            session.add(log)
        session.commit()

        # Create day logs for the last 3 days
        day_logs = []
        for i in range(3):
            log_date = date.today() - timedelta(days=i)
            day_logs.append(DayLog(
                user_id=user.telegram_id,
                date=log_date,
                start_time=datetime.combine(log_date, time(8, 0)),
                end_time=datetime.combine(log_date, time(17, 0)),
                summary=f"Productive day focused on market research and customer interviews. Completed {3 + i} major tasks.",
                highlights=f"Had breakthrough conversation with potential customer. Validated key assumption about market need.",
                challenges="Struggled with time management in the afternoon. Need to improve focus during low-energy periods.",
                learnings="Customer interviews are more valuable than desk research. Direct feedback provides clearer insights.",
                gratitude="Grateful for supportive network and access to potential customers. Appreciate the learning opportunity.",
                tomorrow_plan="Schedule 2 more customer interviews. Start working on competitive analysis report. Review weekly goals.",
                weather="Sunny",
                location="Home office"
            ))
        
        for log in day_logs:
            session.add(log)
        session.commit()

        # Create AI context
        ai_context = AIContext(
            user_id=user.telegram_id,
            behavior_patterns='{"productivity_peaks": ["9:00-11:00", "14:00-16:00"], "energy_dips": ["13:00-14:00", "16:00-17:00"], "preferred_task_types": ["research", "planning"], "avoided_task_types": ["repetitive", "administrative"]}',
            productivity_insights="You perform best during morning hours (9-11 AM) and early afternoon (2-4 PM). Consider scheduling high-energy tasks during these windows and low-energy tasks during your energy dips.",
            motivation_triggers="Progress tracking, customer feedback, and learning new skills significantly boost your motivation. Set up regular check-ins and celebrate small wins.",
            stress_indicators="When you feel overwhelmed, you tend to procrastinate on administrative tasks. Your stress levels increase when you don't see clear progress toward your goals.",
            optimal_work_times="Morning (9-11 AM) for deep work and strategic thinking. Early afternoon (2-4 PM) for creative tasks and customer interactions. Avoid complex tasks during 1-2 PM and 4-5 PM.",
            last_updated=datetime.now()  # IST
        )
        session.add(ai_context)
        session.commit()

        print(f"✅ Created user: {user.name} (ID: {user.telegram_id})")
        print(f"✅ Created job metrics with salary: INR {job_metrics.current_salary}")
        print(f"✅ Created {len(session.exec(select(Goal).where(Goal.user_id == telegram_id)).all())} goals")
        print(f"✅ Created {len(session.exec(select(Task).where(Task.user_id == telegram_id)).all())} tasks")
        print(f"✅ Created {len(session.exec(select(ProgressLog).where(ProgressLog.user_id == telegram_id)).all())} progress logs")
        print(f"✅ Created {len(session.exec(select(DayLog).where(DayLog.user_id == telegram_id)).all())} day logs")
        print(f"✅ Created AI context with behavioral insights")

if __name__ == "__main__":
    print("Starting comprehensive database seeding...")
    print(f"Using database URL: {settings.DATABASE_URL}")
    seed_database()
    print("Database seeding completed successfully!")
    print("\n📊 Sample data includes:")
    print("   • User profile with startup phase tracking")
    print("   • Job metrics with AI analysis")
    print("   • Goals (Yearly, Quarterly, Monthly, Weekly)")
    print("   • Tasks with varying priorities and statuses")
    print("   • 7 days of progress logs")
    print("   • 3 days of detailed day logs")
    print("   • AI context with behavioral insights")