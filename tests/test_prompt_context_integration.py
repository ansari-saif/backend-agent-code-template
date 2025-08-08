from datetime import datetime
from unittest.mock import Mock, patch
from fastapi import status

from app.models.task import Task
from app.models.prompt import Prompt


def test_prompt_includes_todays_tasks_and_prompts_in_context(client, session):
    user_id = "context-user-1"

    # Seed today's tasks
    t1 = Task(user_id=user_id, description="Write unit tests")
    t2 = Task(user_id=user_id, description="Refactor prompt service")
    session.add(t1)
    session.add(t2)
    session.commit()

    # Seed a prior prompt+response from today
    prev = Prompt(user_id=user_id, prompt_text="Prev Q about tasks", response_text="Prev A response")
    session.add(prev)
    session.commit()

    new_prompt_text = "What should I do next given today's progress?"

    with patch("app.services.prompt_service.genai") as mock_genai:
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_model.generate_content = Mock()
        mock_model.generate_content.return_value = Mock(text="Context-aware answer")

        resp = client.post("/prompts/", json={"user_id": user_id, "prompt_text": new_prompt_text})

    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["response_text"] == "Context-aware answer"

    # Verify the model was called with a string containing today's tasks and prompt history
    called_with = mock_model.generate_content.call_args[0][0]
    assert "Write unit tests" in called_with
    assert "Refactor prompt service" in called_with
    assert "Q: Prev Q about tasks" in called_with
    assert "A: Prev A response" in called_with
    assert new_prompt_text in called_with


