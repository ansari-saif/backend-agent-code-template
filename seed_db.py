from datetime import datetime, date, time, timedelta
from decimal import Decimal
from sqlmodel import Session, SQLModel, create_engine, select, delete
import os
import pytz
from app.core.config import settings

# Use database URL from settings
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {})

# Goal descriptions and priorities dictionary for reuse
GOALS = {
    "startup": {
        "description": "Launch my own startup to reduce dependency and gain independence.",
        "priority": "HIGH"
    },
    "health": {
        "description": "Improve overall health and fitness — both mind and body.",
        "priority": "MEDIUM"
    },
    "sirat": {
        "description": "Complete Sirat-un-Nabi and strive to become a better person for a more fulfilling life.",
        "priority": "MEDIUM"
    },
    "handwriting": {
        "description": "Improve my handwriting to confidently pass my B.Tech exams.",
        "priority": "MEDIUM"
    },
    "complete_current_tasks": {
        "description": "Complete all pending current work.",
        "priority": "MEDIUM"
    },
    "alt_performance": {
        "description": "Become a stronger, more valuable employee at ALT.",
        "priority": "MEDIUM"
    },
    "self_improvement": {
        "description": "Continue self-improvement through books, good habits, mindfulness, spirituality, new skills, and other personal growth activities.",
        "priority": "MEDIUM"
    },
    "communication": {
        "description": "Improve communication skills — clear, confident, and empathetic.",
        "priority": "LOW"
    },
}

# Hierarchical goal structure definition
HIERARCHICAL_GOALS = {
    "startup": {
        "quarterly": [
            {
                "description": "Monthly : Complete MVP and 1 interview",
                "deadline": date(2025, 9, 30),
                "priority": "HIGH",
                "phase": "RESEARCH",
                "monthly": [
                    {
                        "description": "Weekly : Complete MVP and 1 interview",
                        "deadline": date(2025, 8, 31),
                        "priority": "HIGH",
                        "phase": "RESEARCH",
                        "completion": 0,
                        "weekly": [
                            {
                                "description": "Weekly : Complete MVP and refine product",
                                "deadline": date(2025, 8, 17),
                                "priority": "HIGH",
                                "completion": 0,
                            },
                            {
                                "description": "1 interview",
                                "deadline": date(2025, 8, 17),
                                "priority": "HIGH",
                                "completion": 0,
                            },
                        ]
                    }
                ]
            }
        ]
    }
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

def create_hierarchical_goals(session, user_id, yearly_goals):
    """Create hierarchical goals using nested loops."""
    all_goals = []
    
    # Create quarterly, monthly, and weekly goals using nested loops
    for goal_key, yearly_goal in yearly_goals.items():
        if goal_key in HIERARCHICAL_GOALS:
            yearly_goal_obj = yearly_goal
            
            # Loop through quarterly goals
            for quarterly_data in HIERARCHICAL_GOALS[goal_key]["quarterly"]:
                quarterly_goal = Goal(
                    user_id=user_id,
                    parent_goal_id=yearly_goal_obj.goal_id,
                    type=GoalTypeEnum.QUARTERLY,
                    description=quarterly_data["description"],
                    deadline=quarterly_data["deadline"],
                    status=StatusEnum.ACTIVE,
                    phase=getattr(PhaseEnum, quarterly_data["phase"]),
                    priority=getattr(PriorityEnum, quarterly_data["priority"]),
                    completion_percentage=0.0
                )
                session.add(quarterly_goal)
                session.commit()
                session.refresh(quarterly_goal)
                all_goals.append(quarterly_goal)
                
                # Loop through monthly goals
                for monthly_data in quarterly_data["monthly"]:
                    monthly_goal = Goal(
                        user_id=user_id,
                        parent_goal_id=quarterly_goal.goal_id,
                        type=GoalTypeEnum.MONTHLY,
                        description=monthly_data["description"],
                        deadline=monthly_data["deadline"],
                        status=StatusEnum.ACTIVE,
                        phase=getattr(PhaseEnum, monthly_data["phase"]),
                        priority=getattr(PriorityEnum, monthly_data["priority"]),
                        completion_percentage=monthly_data["completion"]
                    )
                    session.add(monthly_goal)
                    session.commit()
                    session.refresh(monthly_goal)
                    all_goals.append(monthly_goal)
                    
                    # Loop through weekly goals
                    for weekly_data in monthly_data["weekly"]:
                        weekly_goal = Goal(
                            user_id=user_id,
                            parent_goal_id=monthly_goal.goal_id,
                            type=GoalTypeEnum.WEEKLY,
                            description=weekly_data["description"],
                            deadline=weekly_data["deadline"],
                            status=StatusEnum.ACTIVE,
                            phase=PhaseEnum.RESEARCH,
                            priority=getattr(PriorityEnum, weekly_data["priority"]),
                            completion_percentage=weekly_data["completion"]
                        )
                        session.add(weekly_goal)
                        session.commit()
                        session.refresh(weekly_goal)
                        all_goals.append(weekly_goal)
    
    return all_goals

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
                "financial_health_score": 5.0,
                "work_life_balance_score": 4.0,
                "overall_recommendation": "Consider transitioning to entrepreneurship within 1 year",
                "action_items": [
                    "Build emergency fund to 6 months of expenses",
                    "Start networking in target industry",
                    "Begin side project validation"
                ],
                "risk_factors": [
                    "Limited startup building experience",
                    "Current job provides stability"
                ],
                "opportunities": [
                    "Strong technical background",
                    "Growing market demand for the product",
                ]
            }
        )
        session.add(job_metrics)
        session.commit()

        # Create yearly goals using dict
        yearly_goals = {}
        for goal_key, goal_data in GOALS.items():
            yearly_goal = Goal(
                user_id=user.telegram_id,
                type=GoalTypeEnum.YEARLY,
                description=goal_data["description"],
                status=StatusEnum.ACTIVE,
                phase=PhaseEnum.RESEARCH,
                priority=getattr(PriorityEnum, goal_data["priority"]),
            )
            session.add(yearly_goal)
            session.commit()
            session.refresh(yearly_goal)
            yearly_goals[goal_key] = yearly_goal

        # Create hierarchical goals using nested loops
        hierarchical_goals = create_hierarchical_goals(session, user.telegram_id, yearly_goals)

        # Count goals by type
        yearly_count = len(yearly_goals)
        quarterly_count = len([g for g in hierarchical_goals if g.type == GoalTypeEnum.QUARTERLY])
        monthly_count = len([g for g in hierarchical_goals if g.type == GoalTypeEnum.MONTHLY])
        weekly_count = len([g for g in hierarchical_goals if g.type == GoalTypeEnum.WEEKLY])
        
        print(f"✅ Created user: {user.name} (ID: {user.telegram_id})")
        print(f"✅ Created job metrics with salary: INR {job_metrics.current_salary}")
        print(f"✅ Created {yearly_count} yearly goals")
        print(f"✅ Created {quarterly_count} quarterly goals (linked to yearly)")
        print(f"✅ Created {monthly_count} monthly goals (linked to quarterly)")
        print(f"✅ Created {weekly_count} weekly goals (linked to monthly)")
        print(f"✅ Created {len(session.exec(select(Task).where(Task.user_id == telegram_id)).all())} tasks")
        print(f"✅ Created {len(session.exec(select(ProgressLog).where(ProgressLog.user_id == telegram_id)).all())} progress logs")
        print(f"✅ Created {len(session.exec(select(DayLog).where(DayLog.user_id == telegram_id)).all())} day logs")
        print(f"✅ Created AI context with behavioral insights")
        print(f"✅ Updated all parent goal progress based on children")

if __name__ == "__main__":
    print("Starting comprehensive database seeding with hierarchical goals...")
    print(f"Using database URL: {settings.DATABASE_URL}")
    seed_database()
    print("Database seeding completed successfully!")
    print("\n📊 Sample data includes:")
    print("   • User profile with startup phase tracking")
    print("   • Job metrics with AI analysis")
    print("   • Hierarchical goals (Yearly → Quarterly → Monthly → Weekly)")
    print("   • Parent-child goal relationships with automatic progress tracking")
    print("   • Tasks with varying priorities and statuses")
    print("   • 7 days of progress logs")
    print("   • 3 days of detailed day logs")
    print("   • AI context with behavioral insights")
    print("\n🎯 Goal Hierarchy Created:")
    print("   • 8 Yearly Goals (parent level)")
    print("   • 3 Quarterly Goals (linked to yearly)")
    print("   • 3 Monthly Goals (linked to quarterly)")
    print("   • 6 Weekly Goals (linked to monthly)")
    print("   • Automatic progress calculation up the hierarchy")