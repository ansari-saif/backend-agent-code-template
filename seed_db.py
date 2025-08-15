from datetime import datetime, date, time, timedelta
from decimal import Decimal
from sqlmodel import Session, SQLModel, create_engine, select, delete
import os
import pytz
from app.core.config import settings

# Use database URL from settings
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {})

# Goal descriptions dictionary for reuse
GOALS = {
    "health": "Improve overall health and fitness — both mind and body.",
    "sirat": "Complete Sirat-un-Nabi and strive to become a better person for a more fulfilling life.",
    "startup": "Launch my own startup to reduce dependency and gain independence.",
    "handwriting": "Improve my handwriting to confidently pass my B.Tech exams.",
    "alt_backlog": "Complete all pending ALT work.",
    "alt_performance": "Become a stronger, more valuable employee at ALT.",
    "self_improvement": "Continue self-improvement through books, good habits, mindfulness, spirituality, new skills, and other personal growth activities.",
    "communication": "Improve communication skills — clear, confident, and empathetic.",
}

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
    # Bulk deletes for better performance
    session.exec(delete(Task).where(Task.user_id == telegram_id))
    session.exec(delete(ProgressLog).where(ProgressLog.user_id == telegram_id))
    session.exec(delete(DayLog).where(DayLog.user_id == telegram_id))
    session.exec(delete(AIContext).where(AIContext.user_id == telegram_id))
    session.exec(delete(Goal).where(Goal.user_id == telegram_id))
    session.exec(delete(JobMetrics).where(JobMetrics.user_id == telegram_id))
    session.exec(delete(User).where(User.telegram_id == telegram_id))
    session.commit()

def seed_database():
    # Create tables if they don't exist
    create_db_and_tables()
    
    # Set up IST timezone
    ist = pytz.timezone("Asia/Kolkata")
    
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
            last_updated=datetime.now(ist),  # IST
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

        # Create yearly goals using dict
        yearly_goals = []
        for goal_key in GOALS:
            yearly_goals.append(Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.YEARLY,
                description=GOALS[goal_key],
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.MEDIUM,
            ))
        session.add_all(yearly_goals)
        session.commit()
        session.flush()  # Ensure IDs are available

        # Quarter deadlines
        q1_deadline = date(2025, 3, 31)
        q2_deadline = date(2025, 6, 30)
        q3_deadline = date(2025, 9, 30)
        q4_deadline = date(2025, 12, 31)

        # Create quarterly goals: 3 focus + maintenance
        quarterly_goals = []
        
        # Q1 Focus Goals (3 main areas)
        q1_focus_goals = [
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Startup Validation: 20 interviews, 3 solution experiments, landing page (no MVP yet)",
                deadline=q1_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.HIGH,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Health & Fitness: 5 workouts/week, daily mindfulness, +10% stamina target",
                deadline=q1_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.HIGH,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="ALT Backlog: Clear 100% pending work with weekly progress reports",
                deadline=q1_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.HIGH,
            ),
        ]
        quarterly_goals.extend(q1_focus_goals)
        
        # Q1 Maintenance Goals (simpler, lower priority)
        q1_maintenance_goals = [
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Sirat-un-Nabi: 2 chapters/week (habit maintenance)",
                deadline=q1_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.LOW,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Handwriting: 20 mins twice a week",
                deadline=q1_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.LOW,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Self-improvement: 1 book this quarter",
                deadline=q1_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.LOW,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Communication: 1 speaking drill/week",
                deadline=q1_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.LOW,
            ),
        ]
        quarterly_goals.extend(q1_maintenance_goals)
        
        # Q2 Focus Goals (3 main areas)
        q2_focus_goals = [
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Startup MVP: Build slice, onboard 5-10 users",
                deadline=q2_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.MVP,
                priority=PriorityEnum.HIGH,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Communication: Intensive training - 3 drills/week, 1 recording/week, 2 writing/week",
                deadline=q2_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.HIGH,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="ALT Performance: Exceed 2 KPIs, deliver 1 process improvement",
                deadline=q2_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.HIGH,
            ),
        ]
        quarterly_goals.extend(q2_focus_goals)
        
        # Q2 Maintenance Goals
        q2_maintenance_goals = [
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Health: 3 workouts/week (maintenance)",
                deadline=q2_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.LOW,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Sirat-un-Nabi: 1 chapter/week",
                deadline=q2_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.LOW,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Handwriting: 20 mins weekly",
                deadline=q2_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.LOW,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Self-improvement: Casual reading, no new habits",
                deadline=q2_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.LOW,
            ),
        ]
        quarterly_goals.extend(q2_maintenance_goals)
        
        # Q3 Focus Goals (3 main areas)
        q3_focus_goals = [
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Sirat-un-Nabi: 50% completion with deep reading and reflection notes",
                deadline=q3_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.HIGH,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Self-improvement: 2 new habits (track streaks), finish 2 books",
                deadline=q3_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.HIGH,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Health: Increase difficulty, add strength training",
                deadline=q3_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.HIGH,
            ),
        ]
        quarterly_goals.extend(q3_focus_goals)
        
        # Q3 Maintenance Goals
        q3_maintenance_goals = [
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Startup: 2-3 customer interviews/month for feedback",
                deadline=q3_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.LOW,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="ALT Backlog: Keep <10% pending",
                deadline=q3_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.LOW,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Communication: 1 drill/week",
                deadline=q3_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.LOW,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Handwriting: 20 mins/week",
                deadline=q3_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.LOW,
            ),
        ]
        quarterly_goals.extend(q3_maintenance_goals)
        
        # Q4 Focus Goals (3 main areas)
        q4_focus_goals = [
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Startup Revenue: Monetize MVP, aim for first paying customers",
                deadline=q4_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.GROWTH,
                priority=PriorityEnum.HIGH,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Handwriting: Daily 20 mins for B.Tech prep, 2 mock exams/month",
                deadline=q4_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.HIGH,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="ALT Performance: Year-end KPI push, one major process improvement",
                deadline=q4_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.HIGH,
            ),
        ]
        quarterly_goals.extend(q4_focus_goals)
        
        # Q4 Maintenance Goals
        q4_maintenance_goals = [
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Health: 3 workouts/week",
                deadline=q4_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.LOW,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Sirat-un-Nabi: 1 chapter/week",
                deadline=q4_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.LOW,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Self-improvement: 1 book",
                deadline=q4_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.LOW,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.QUARTERLY,
                description="Communication: 1 recording/month",
                deadline=q4_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.LOW,
            ),
        ]
        quarterly_goals.extend(q4_maintenance_goals)
        
        session.add_all(quarterly_goals)
        session.commit()
        session.flush()  # Ensure IDs are available
        
        # Keep references for task linking
        q1_goal = q1_focus_goals[0]  # Startup validation
        q2_goal = q2_focus_goals[0]  # Startup MVP

        # Compute month and week deadlines
        today = date.today()
        first_of_next_month = date(today.year + (1 if today.month == 12 else 0),
                                   1 if today.month == 12 else today.month + 1,
                                   1)
        month_deadline = first_of_next_month - timedelta(days=1)
        days_to_sunday = 6 - today.weekday()
        week_deadline = today + timedelta(days=days_to_sunday)

        # Create monthly goals aligned with yearly goals
        monthly_goals = [
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.MONTHLY,
                description="Health: complete 20 workouts and 25 mindfulness sessions.",
                deadline=month_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.MEDIUM,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.MONTHLY,
                description="Sirat-un-Nabi: read 8 chapters with notes and monthly reflections.",
                deadline=month_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.MEDIUM,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.MONTHLY,
                description="Startup: ship MVP slice and collect 10 user signups/feedback.",
                deadline=month_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.MVP,
                priority=PriorityEnum.HIGH,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.MONTHLY,
                description="Handwriting: daily 20 minutes; complete 10 practice sheets.",
                deadline=month_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.MEDIUM,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.MONTHLY,
                description="ALT backlog: clear 100% of pending work and report weekly.",
                deadline=month_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.HIGH,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.MONTHLY,
                description="ALT performance: exceed 2 KPIs and deliver 1 process improvement.",
                deadline=month_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.MEDIUM,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.MONTHLY,
                description="Self-improvement: finish 1 book and maintain 2 habits (21+ day streak).",
                deadline=month_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.MEDIUM,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.MONTHLY,
                description="Communication: 30 daily speaking drills, 4 recordings with feedback, and 8 writing exercises.",
                deadline=month_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.MEDIUM,
            ),
        ]
        session.add_all(monthly_goals)
        session.commit()
        session.flush()
        
        # Keep a reference for tasks below (startup-related monthly goal)
        monthly_goal = monthly_goals[2]
        # Reference for communication monthly goal
        communication_monthly_goal = monthly_goals[7]

        # Create weekly goals aligned with yearly goals
        weekly_goals = [
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.WEEKLY,
                description="Health: 5 workouts and 7 mindfulness sessions this week.",
                deadline=week_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.MEDIUM,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.WEEKLY,
                description="Sirat-un-Nabi: read 2 chapters and write reflections.",
                deadline=week_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.MEDIUM,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.WEEKLY,
                description="Startup: conduct 5 interviews and validate 1 key hypothesis.",
                deadline=week_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.HIGH,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.WEEKLY,
                description="Handwriting: 20 minutes daily; complete 2 mock answer sheets.",
                deadline=week_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.MEDIUM,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.WEEKLY,
                description="ALT backlog: clear at least 30% this week and update status.",
                deadline=week_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.HIGH,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.WEEKLY,
                description="ALT performance: exceed 1 KPI and propose 1 improvement.",
                deadline=week_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.MEDIUM,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.WEEKLY,
                description="Self-improvement: read 3 chapters and maintain 2 habits daily.",
                deadline=week_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.MEDIUM,
            ),
            Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.WEEKLY,
                description="Communication: daily 10m speaking drills, 1 recording with feedback, and 2 writing exercises.",
                deadline=week_deadline,
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=PriorityEnum.MEDIUM,
            ),
        ]
        session.add_all(weekly_goals)
        session.commit()
        session.flush()
        
        # Keep a reference for tasks below (startup-related weekly goal)
        weekly_goal = weekly_goals[2]

        # Helpful references for tasks linked to monthly focus areas
        health_monthly_goal = monthly_goals[0]
        sirat_monthly_goal = monthly_goals[1]
        startup_monthly_goal = monthly_goal
        handwriting_monthly_goal = monthly_goals[3]
        alt_backlog_monthly_goal = monthly_goals[4]
        alt_perf_monthly_goal = monthly_goals[5]
        self_improve_monthly_goal = monthly_goals[6]
        communication_monthly_goal = monthly_goals[7]

        # Create tasks aligned with current goals
        tasks = [
            # Startup / Entrepreneurship
            Task(
                user_id=user.telegram_id,
                goal_id=q1_goal.goal_id,
                description="Draft interview script and schedule 5 customer interviews",
                priority=TaskPriorityEnum.HIGH,
                completion_status=CompletionStatusEnum.IN_PROGRESS,
                estimated_duration=90,
                actual_duration=45,
                energy_required=EnergyRequiredEnum.MEDIUM,
                scheduled_for_date=today,
                started_at=datetime(today.year, today.month, today.day, 11, 0),
                ai_generated=True
            ),
            Task(
                user_id=user.telegram_id,
                goal_id=weekly_goal.goal_id,
                description="Conduct 2 customer interviews and synthesize notes",
                priority=TaskPriorityEnum.URGENT,
                completion_status=CompletionStatusEnum.PENDING,
                estimated_duration=120,
                energy_required=EnergyRequiredEnum.MEDIUM,
                scheduled_for_date=today + timedelta(days=1),
                ai_generated=False
            ),
            Task(
                user_id=user.telegram_id,
                goal_id=q2_goal.goal_id,
                description="Implement MVP slice: auth + basic dashboard",
                priority=TaskPriorityEnum.MEDIUM,
                completion_status=CompletionStatusEnum.PENDING,
                estimated_duration=240,
                energy_required=EnergyRequiredEnum.HIGH,
                scheduled_for_date=today + timedelta(days=3),
                ai_generated=True
            ),
            Task(
                user_id=user.telegram_id,
                goal_id=startup_monthly_goal.goal_id,
                description="Launch landing page and collect first 10 signups",
                priority=TaskPriorityEnum.HIGH,
                completion_status=CompletionStatusEnum.PENDING,
                estimated_duration=180,
                energy_required=EnergyRequiredEnum.MEDIUM,
                scheduled_for_date=today + timedelta(days=5),
                ai_generated=False
            ),

            # Health & Fitness
            Task(
                user_id=user.telegram_id,
                goal_id=health_monthly_goal.goal_id,
                description="Workout: 45-minute full-body session",
                priority=TaskPriorityEnum.MEDIUM,
                completion_status=CompletionStatusEnum.COMPLETED,
                estimated_duration=60,
                actual_duration=45,
                energy_required=EnergyRequiredEnum.HIGH,
                scheduled_for_date=today,
                started_at=datetime(today.year, today.month, today.day, 7, 0),
                completed_at=datetime(today.year, today.month, today.day, 7, 45),
                ai_generated=False
            ),
            Task(
                user_id=user.telegram_id,
                goal_id=health_monthly_goal.goal_id,
                description="Mindfulness: 10-minute breathing session",
                priority=TaskPriorityEnum.LOW,
                completion_status=CompletionStatusEnum.PENDING,
                estimated_duration=15,
                energy_required=EnergyRequiredEnum.LOW,
                scheduled_for_date=today,
                ai_generated=False
            ),

            # Sirat-un-Nabi
            Task(
                user_id=user.telegram_id,
                goal_id=sirat_monthly_goal.goal_id,
                description="Read 2 chapters of Sirat-un-Nabi and write reflections",
                priority=TaskPriorityEnum.MEDIUM,
                completion_status=CompletionStatusEnum.PENDING,
                estimated_duration=90,
                energy_required=EnergyRequiredEnum.LOW,
                scheduled_for_date=today + timedelta(days=2),
                ai_generated=False
            ),

            # Handwriting
            Task(
                user_id=user.telegram_id,
                goal_id=handwriting_monthly_goal.goal_id,
                description="Handwriting practice: 20 minutes + 1 mock answer sheet",
                priority=TaskPriorityEnum.MEDIUM,
                completion_status=CompletionStatusEnum.PENDING,
                estimated_duration=40,
                energy_required=EnergyRequiredEnum.MEDIUM,
                scheduled_for_date=today + timedelta(days=1),
                ai_generated=False
            ),

            # ALT work & performance
            Task(
                user_id=user.telegram_id,
                goal_id=alt_backlog_monthly_goal.goal_id,
                description="ALT: clear 5 backlog items and update tracker",
                priority=TaskPriorityEnum.URGENT,
                completion_status=CompletionStatusEnum.IN_PROGRESS,
                estimated_duration=180,
                actual_duration=60,
                energy_required=EnergyRequiredEnum.MEDIUM,
                scheduled_for_date=today,
                started_at=datetime(today.year, today.month, today.day, 15, 0),
                ai_generated=False
            ),
            Task(
                user_id=user.telegram_id,
                goal_id=alt_perf_monthly_goal.goal_id,
                description="ALT: propose 1 process improvement and draft plan",
                priority=TaskPriorityEnum.MEDIUM,
                completion_status=CompletionStatusEnum.PENDING,
                estimated_duration=90,
                energy_required=EnergyRequiredEnum.LOW,
                scheduled_for_date=today + timedelta(days=2),
                ai_generated=False
            ),

            # Self improvement
            Task(
                user_id=user.telegram_id,
                goal_id=self_improve_monthly_goal.goal_id,
                description="Read 3 chapters of a self-improvement book and summarize notes",
                priority=TaskPriorityEnum.LOW,
                completion_status=CompletionStatusEnum.PENDING,
                estimated_duration=120,
                energy_required=EnergyRequiredEnum.LOW,
                scheduled_for_date=today + timedelta(days=3),
                ai_generated=False
            ),
            # Communication
            Task(
                user_id=user.telegram_id,
                goal_id=communication_monthly_goal.goal_id,
                description="Communication practice: record a 3-minute talk and self-review",
                priority=TaskPriorityEnum.MEDIUM,
                completion_status=CompletionStatusEnum.PENDING,
                estimated_duration=30,
                energy_required=EnergyRequiredEnum.LOW,
                scheduled_for_date=today + timedelta(days=1),
                ai_generated=False
            ),
        ]
        
        session.add_all(tasks)
        session.commit()

        # Create progress logs for the last 7 days (aligned with goals)
        progress_logs = []
        for i in range(7):
            log_date = date.today() - timedelta(days=i)
            progress_logs.append(ProgressLog(
                user_id=user.telegram_id,
                date=log_date,
                tasks_completed=2 + (i % 3),
                tasks_planned=5,
                mood_score=6 + (i % 2),
                energy_level=6 + (i % 3),
                focus_score=6 + (i % 2),
                daily_reflection=(
                    f"Day {i+1}: Completed workout and mindfulness. "
                    f"Read Sirat-un-Nabi and progressed startup interviews. Practiced handwriting."
                ),
                ai_insights=(
                    f"AI Insight Day {i+1}: Morning deep work worked well. "
                    f"Keep workouts at 7 AM and schedule interviews between 11 AM - 1 PM for best energy."
                )
            ))
        
        session.add_all(progress_logs)
        session.commit()

        # Create day logs for the last 3 days (aligned with goals)
        day_logs = []
        for i in range(3):
            log_date = date.today() - timedelta(days=i)
            day_logs.append(DayLog(
                user_id=user.telegram_id,
                date=log_date,
                start_time=datetime.combine(log_date, time(8, 0)),
                end_time=datetime.combine(log_date, time(17, 0)),
                summary=f"Balanced day: workout + mindfulness, startup interviews, and handwriting practice. Completed {3 + i} tasks.",
                highlights=f"Great interview insights and strong workout routine maintained.",
                challenges="Energy dip post-lunch; handwriting practice felt slow.",
                learnings="Short mindful breaks boost focus; interviewing yields better startup direction.",
                gratitude="Health, learning opportunities, and supportive colleagues at ALT.",
                tomorrow_plan="Finish interview scheduling, ship MVP slice, and complete 20-min handwriting practice.",
                weather="Sunny",
                location="Home office"
            ))
        
        session.add_all(day_logs)
        session.commit()

        # Create AI context aligned with current goals
        ai_context = AIContext(
            user_id=user.telegram_id,
            behavior_patterns='{"productivity_peaks": ["7:00-9:00", "10:00-12:00"], "energy_dips": ["13:00-14:00"], "health_routine": {"workouts_per_week": 5, "mindfulness_daily": true}, "learning_focus": ["Sirat-un-Nabi", "self-improvement books"], "skill_habits": ["handwriting 20m daily"], "work_focus": {"ALT": ["clear backlog", "exceed KPIs"], "startup": ["interviews", "MVP slices"]}}',
            productivity_insights="Best flow: workout 7-8 AM, deep work 10 AM–12 PM for interviews/MVP, admin 3-5 PM. Handwriting practice is easiest in the evening.",
            motivation_triggers="Visible progress (signup count, interview count), habit streaks, spiritual reading, and positive feedback at ALT.",
            stress_indicators="Backlog growing at ALT, missed workouts >2 days, unclear MVP scope, or delayed interview responses increase stress.",
            optimal_work_times="Workout 7-8 AM; Deep work 10-12; Meetings/interviews 11-13; Admin 15-17; Avoid complex work 13-14.",
            last_updated=datetime.now(ist)  # IST
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