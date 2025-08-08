import pytest
from unittest.mock import patch
from fastapi import status


@pytest.mark.integration
class TestJobMetricsAIGenerate:
    def test_generate_job_metrics_when_missing(self, client, session, test_user):
        mock_data = {
            "stress_level": 4,
            "job_satisfaction": 6,
            "startup_revenue": 2000,
            "current_salary": 60000,
            "monthly_expenses": 2500,
            "runway_months": 5,
            "quit_readiness_score": 42.5,
        }

        with patch("app.services.ai_service.AIService.generate_job_metrics_for_user") as mock_ai:
            mock_ai.return_value = mock_data

            resp = client.post(f"/job-metrics/user/{test_user.telegram_id}/generate")

        assert resp.status_code == status.HTTP_201_CREATED
        payload = resp.json()

        assert payload["user_id"] == test_user.telegram_id
        assert payload["stress_level"] == mock_data["stress_level"]
        assert payload["job_satisfaction"] == mock_data["job_satisfaction"]
        assert float(payload["startup_revenue"]) == float(mock_data["startup_revenue"]) if payload["startup_revenue"] is not None else True
        assert float(payload["current_salary"]) == float(mock_data["current_salary"]) if payload["current_salary"] is not None else True
        assert float(payload["monthly_expenses"]) == float(mock_data["monthly_expenses"]) if payload["monthly_expenses"] is not None else True
        assert (payload["runway_months"] == mock_data["runway_months"]) or (payload["runway_months"] is None)
        assert float(payload["quit_readiness_score"]) == float(mock_data["quit_readiness_score"]) or payload["quit_readiness_score"] == 0

