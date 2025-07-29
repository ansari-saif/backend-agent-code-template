from sqlmodel import Session, select, SQLModel, create_engine
import os
from app.core.config import settings

# Use database URL from settings
engine = create_engine(settings.DATABASE_URL)

from app.models.user import User
from app.models.goal import Goal
from app.models.job_metrics import JobMetrics

def create_db_and_tables():
    """Create database and all tables."""
    SQLModel.metadata.create_all(engine)

def read_database():
    # Ensure tables exist
    create_db_and_tables()
    
    with Session(engine) as session:
        # Read all users
        users = session.exec(select(User)).all()
        if not users:
            print("No users found in the database!")
            return
            
        for user in users:
            print("\n=== User Profile ===")
            print(f"Name: {user.name}")
            print(f"Telegram ID: {user.telegram_id}")
            print(f"Current Phase: {user.current_phase}")
            print(f"Timezone: {user.timezone}")
            print(f"Energy Profile: {user.energy_profile}")
            print(f"Onboarding Complete: {user.onboarding_complete}")

            # Read job metrics
            job_metrics = session.exec(select(JobMetrics).where(JobMetrics.user_id == user.telegram_id)).first()
            if job_metrics:
                print("\n=== Job Metrics ===")
                print(f"Current Salary: ${job_metrics.current_salary:,.2f}")
                print(f"Startup Revenue: ${job_metrics.startup_revenue:,.2f}")
                print(f"Runway Months: {job_metrics.runway_months}")
                print(f"Stress Level (1-10): {job_metrics.stress_level}")
                print(f"Job Satisfaction (1-10): {job_metrics.job_satisfaction}")
                print(f"Last Updated: {job_metrics.last_updated}")
            else:
                print("\nNo job metrics found!")

            # Read goals
            goals = session.exec(select(Goal).where(Goal.user_id == user.telegram_id)).all()
            if goals:
                print("\n=== Goals ===")
                for goal in goals:
                    print(f"\nType: {goal.type}")
                    print(f"Description: {goal.description}")
                    print(f"Deadline: {goal.deadline}")
                    print(f"Status: {goal.status}")
                    print(f"Phase: {goal.phase}")
                    print(f"Priority: {goal.priority}")
                    print(f"Completion: {goal.completion_percentage}%")
            else:
                print("\nNo goals found!")

if __name__ == "__main__":
    print("Reading database contents...")
    print(f"Using database URL: {settings.DATABASE_URL}")
    read_database()