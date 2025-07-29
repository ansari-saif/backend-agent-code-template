from datetime import datetime, date
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
from app.models.job_metrics import JobMetrics

def cleanup_existing_data(session, telegram_id):
    """Remove existing data for the given telegram_id"""
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
        telegram_id = "saif_126"
        
        # Clean up existing data
        cleanup_existing_data(session, telegram_id)
        
        # Create user
        user = User(
            telegram_id=telegram_id,
            name="Saif Husain test",

            timezone=TimezoneEnum.IST,
            current_phase=PhaseEnum.RESEARCH,
            energy_profile=EnergyProfileEnum.MORNING,
            onboarding_complete=True
        )
        session.add(user)
        session.commit()

        # Create job metrics
        job_metrics = JobMetrics(
            user_id=user.telegram_id,
            current_salary=Decimal("120000"),
            startup_revenue=Decimal("0"),
            runway_months=1.0,
            stress_level=5,  # Default middle value
            job_satisfaction=7,  # Assuming relatively satisfied with current job
            last_updated=datetime.utcnow()
        )
        session.add(job_metrics)
        session.commit()

        # Create main goal
        main_goal = Goal(
            user_id=user.telegram_id,
            type=GoalTypeEnum.YEARLY,
            description="Build a successful startup within a year",
            deadline=date(2025, 5, 1),  # Set to one year from now
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.HIGH,
            completion_percentage=0.0
        )
        session.add(main_goal)

        # Create supporting quarterly goals
        q1_goal = Goal(
            user_id=user.telegram_id,
            type=GoalTypeEnum.QUARTERLY,
            description="Complete market research and validate business idea",
            deadline=date(2024, 8, 1),  # 3 months from now
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.HIGH,
            completion_percentage=0.0
        )
        session.add(q1_goal)

        q2_goal = Goal(
            user_id=user.telegram_id,
            type=GoalTypeEnum.QUARTERLY,
            description="Develop MVP and get initial user feedback",
            deadline=date(2024, 11, 1),  # 6 months from now
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.MVP,
            priority=PriorityEnum.HIGH,
            completion_percentage=0.0
        )
        session.add(q2_goal)

        session.commit()

if __name__ == "__main__":
    print("Starting database seeding...")
    print(f"Using database URL: {settings.DATABASE_URL}")
    seed_database()
    print("Database seeding completed successfully!")