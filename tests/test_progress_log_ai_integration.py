import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi import status

from app.models.user import User
from app.schemas.goal import GoalTypeEnum, PhaseEnum
from app.models.goal import Goal
from app.models.task import Task
from app.models.job_metrics import JobMetrics
from app.models.day_log import DayLog
from app.models.log import Log
from app.models.progress_log import ProgressLog

@pytest.mark.integration
class TestProgressLogAIIntegration:
    def test_auto_generate_progress_log(self, client, session, test_user):
        """
        Test the complete flow of automatically generating a ProgressLog using AI:
        1. Setup test data (goals, tasks, job metrics, day log)
        2. Call the AI endpoint
        3. Verify the generated ProgressLog
        """
        # Setup: Create a goal
        goal = Goal(
            user_id=test_user.telegram_id,
            type=GoalTypeEnum.MONTHLY,
            description="Finish implementing key features",
            deadline=datetime.utcnow() + timedelta(days=7),
            phase=PhaseEnum.MVP,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(goal)
        session.commit()

        # Create tasks
        task1 = Task(
            user_id=test_user.telegram_id,
            description="Implement feature A",
            priority="HIGH",
            energy_required="MEDIUM",
            completion_status="COMPLETED",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        task2 = Task(
            user_id=test_user.telegram_id,
            description="Implement feature B",
            priority="MEDIUM",
            energy_required="LOW",
            completion_status="IN_PROGRESS",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(task1)
        session.add(task2)
        session.commit()

        # Create job metrics
        job_metrics = JobMetrics(
            user_id=test_user.telegram_id,
            stress_level=3,
            job_satisfaction=7,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(job_metrics)
        session.commit()

        # Create day log
        now = datetime.utcnow()
        day_log = DayLog(
            user_id=test_user.telegram_id,
            date=now.date(),
            start_time=now,
            created_at=now,
            updated_at=now
        )
        session.add(day_log)
        session.commit()

        # Create a log
        log = Log(
            title="Daily Progress",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(log)
        session.commit()

        # Mock AI response
        mock_progress_data = {
            "achievements": ["Completed feature A implementation", "Started work on feature B"],
            "challenges": ["Some technical difficulties in feature B"],
            "learnings": ["Learned new testing patterns", "Improved code organization"],
            "next_steps": ["Complete feature B", "Start planning feature C"],
            "mood_analysis": "Positive and productive day with good energy levels",
            "productivity_insights": "High productivity with good task completion rate"
        }

        # Test the AI endpoint
        with patch("app.services.ai_service.AIService.generate_progress_log_content") as mock_ai:
            mock_ai.return_value = mock_progress_data
            
            response = client.post(
                f"/progress-logs/generate/{test_user.telegram_id}",
                json={"date": datetime.utcnow().date().isoformat()}
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            created_log = response.json()
            
            # Verify the response structure
            assert "log_id" in created_log
            assert created_log["daily_reflection"] == "\n".join([
                "Achievements:",
                *[f"- {a}" for a in mock_progress_data["achievements"]],
                "\nChallenges:",
                *[f"- {c}" for c in mock_progress_data["challenges"]],
                "\nLearnings:",
                *[f"- {l}" for l in mock_progress_data["learnings"]],
                "\nNext Steps:",
                *[f"- {n}" for n in mock_progress_data["next_steps"]]
            ])
            assert created_log["ai_insights"] == f"{mock_progress_data['mood_analysis']}\n\n{mock_progress_data['productivity_insights']}"
            
            # Verify the log was saved in the database
            db_log = session.query(ProgressLog).filter(
                ProgressLog.log_id == created_log["log_id"]
            ).first()
            assert db_log is not None
            assert db_log.user_id == test_user.telegram_id
