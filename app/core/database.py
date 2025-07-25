from sqlmodel import SQLModel, create_engine, Session
from typing import Annotated
from fastapi import Depends
import os

# Import all models to ensure they're registered
from app.models.todo import Todo
from app.models.user import User
from app.models.goal import Goal
from app.models.task import Task
from app.models.progress_log import ProgressLog
from app.models.ai_context import AIContext
from app.models.job_metrics import JobMetrics

# Use SQLite for development, PostgreSQL for production
database_url = os.getenv("DATABASE_URL", "")

# Create engine
connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(database_url, connect_args=connect_args, echo=True)

def create_db_and_tables():
    """Create database and all tables."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Get database session."""
    with Session(engine) as session:
        yield session
