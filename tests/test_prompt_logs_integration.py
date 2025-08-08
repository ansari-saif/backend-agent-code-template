import pytest
from unittest.mock import Mock, patch
from fastapi import status
from app.models.log import Log


@pytest.mark.integration
def test_prompt_creates_valuable_log(client, session):
    payload = {"user_id": "u1", "prompt_text": "Summarize today's key insights and next steps."}

    with patch("app.services.prompt_service.genai") as mock_genai:
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_model.generate_content = Mock()
        # Long response triggers logging heuristic
        mock_model.generate_content.return_value = Mock(text="""
        Key insights: We validated the core assumption and users prefer flow A over B. 
        Next steps: ship experiment to 20 more users and measure conversion.
        """.strip())

        resp = client.post("/prompts/", json=payload)

    assert resp.status_code == status.HTTP_201_CREATED

    # A Log entry should exist
    logs = session.exec(Log.__table__.select()).all()
    assert len(logs) >= 1
    assert any("Key insights" in (row.title or "") for row in logs)


@pytest.mark.integration
def test_prompt_skips_nonvaluable_log(client, session):
    payload = {"user_id": "u2", "prompt_text": "Say hi"}

    with patch("app.services.prompt_service.genai") as mock_genai:
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_model.generate_content = Mock()
        mock_model.generate_content.return_value = Mock(text="Hi")

        resp = client.post("/prompts/", json=payload)

    assert resp.status_code == status.HTTP_201_CREATED

    # No logs created because response is trivial
    logs = session.exec(Log.__table__.select()).all()
    assert len(logs) == 0

