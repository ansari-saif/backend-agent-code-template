import pytest
import pytest_asyncio
from unittest.mock import Mock, patch
from fastapi import status
from sqlmodel import Session
from app.models.job_metrics import JobMetrics
from app.models.user import User
from app.services.ai_service import AIService
from app.services.job_metrics_service import analyze_job_metrics_with_ai
from datetime import datetime, date, UTC
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_session

@pytest.fixture
def test_client(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(session: Session, sample_user_data):
    """Create a test user in the database."""
    user = User(**sample_user_data)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.mark.integration
def test_analyze_job_metrics_with_ai_success(session: Session, test_user, test_client, sample_job_metrics_data):
    # Create test job metrics
    data = sample_job_metrics_data.copy()
    data["user_id"] = test_user.telegram_id
    job_metrics = JobMetrics(**data)
    session.add(job_metrics)
    session.commit()
    session.refresh(job_metrics)

    # Mock AI service response
    mock_analysis = {
        "financial_readiness": "Medium",
        "personal_readiness": "High",
        "overall_recommendation": "Wait",
        "risk_level": "Medium",
        "key_strengths": ["Strong financial planning", "Good stress management"],
        "action_items": ["Increase revenue", "Build emergency fund"],
        "confidence_score": 75
    }

    with patch("app.services.ai_service.AIService") as mock_ai_service:
        mock_instance = Mock()
        mock_ai_service.return_value = mock_instance
        mock_instance.analyze_career_transition_readiness = Mock()
        mock_instance.analyze_career_transition_readiness.return_value = mock_analysis

        # Call the endpoint
        response = test_client.post(f"/job-metrics/{job_metrics.metric_id}/analyze")
        if response.status_code != status.HTTP_200_OK:
            print(f"Error response: {response.json()}")
        assert response.status_code == status.HTTP_200_OK

        # Verify response
        data = response.json()
        assert data["ai_analysis"]["career_growth_score"] == 0.8  # 75/100
        assert data["ai_analysis"]["financial_health_score"] == 0.5  # Medium
        assert data["ai_analysis"]["work_life_balance_score"] == 1.0  # High
        assert data["ai_analysis"]["overall_recommendation"] == "Wait"
        assert len(data["ai_analysis"]["action_items"]) == 2
        assert "Increase revenue" in data["ai_analysis"]["action_items"]
        assert "Build emergency fund" in data["ai_analysis"]["action_items"]
        assert len(data["ai_analysis"]["risk_factors"]) == 1
        assert data["ai_analysis"]["risk_factors"][0] == "Medium"
        assert len(data["ai_analysis"]["opportunities"]) == 2
        assert "Strong financial planning" in data["ai_analysis"]["opportunities"]
        assert "Good stress management" in data["ai_analysis"]["opportunities"]

@pytest.mark.integration
def test_analyze_job_metrics_with_ai_not_found(test_client):
    # Try to analyze non-existent metrics
    response = test_client.post("/job-metrics/999999/analyze")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()

@pytest.mark.integration
def test_analyze_job_metrics_with_ai_error_handling(session: Session, test_user, test_client, sample_job_metrics_data):
    # Create test job metrics
    data = sample_job_metrics_data.copy()
    data["user_id"] = test_user.telegram_id
    job_metrics = JobMetrics(**data)
    session.add(job_metrics)
    session.commit()
    session.refresh(job_metrics)

    # Mock AI service to raise an exception
    with patch("app.services.ai_service.AIService.analyze_career_transition_readiness") as mock_analyze:
        mock_analyze.side_effect = Exception("AI service error")

        # Call the endpoint
        response = test_client.post(f"/job-metrics/{job_metrics.metric_id}/analyze")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "error analyzing job metrics" in response.json()["detail"].lower()

@pytest.mark.integration
def test_analyze_job_metrics_with_ai_user_not_found(session: Session, test_client, sample_job_metrics_data):
    # Create job metrics with non-existent user
    data = sample_job_metrics_data.copy()
    data["user_id"] = "non_existent_user"
    job_metrics = JobMetrics(**data)
    session.add(job_metrics)
    session.commit()
    session.refresh(job_metrics)

    # Call the endpoint
    response = test_client.post(f"/job-metrics/{job_metrics.metric_id}/analyze")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "user not found" in response.json()["detail"].lower()