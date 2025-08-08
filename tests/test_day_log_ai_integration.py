import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from fastapi import status

from app.models.day_log import DayLog


@pytest.mark.integration
class TestDayLogAIIntegration:
    def test_generate_day_log_with_ai(self, client, session, test_user):
        # Arrange: mock AI content
        mock_content = {
            "summary": "Good focus with steady progress.",
            "highlights": "- Finished feature A\n- Wrote tests",
            "challenges": "- Integration setup took longer",
            "learnings": "- Better to mock external deps",
            "gratitude": "Grateful for productive time.",
            "tomorrow_plan": "- Complete feature B\n- Review PRs",
        }

        today = datetime.utcnow().date()

        with patch("app.services.ai_service.AIService.generate_day_log_content") as mock_ai:
            mock_ai.return_value = mock_content

            # Act
            resp = client.post(f"/day-logs/generate/{test_user.telegram_id}", json={"date": today.isoformat()})

        # Assert
        assert resp.status_code == status.HTTP_201_CREATED
        payload = resp.json()
        assert payload["user_id"] == test_user.telegram_id
        assert payload["date"] == today.isoformat()
        assert payload["summary"] == mock_content["summary"]
        assert payload["highlights"] == mock_content["highlights"]
        assert payload["challenges"] == mock_content["challenges"]
        assert payload["learnings"] == mock_content["learnings"]
        assert payload["gratitude"] == mock_content["gratitude"]
        assert payload["tomorrow_plan"] == mock_content["tomorrow_plan"]

        # Check DB record exists
        db_obj = session.exec(
            DayLog.__table__.select().where(DayLog.user_id == test_user.telegram_id, DayLog.date == today)
        ).first()
        assert db_obj is not None

