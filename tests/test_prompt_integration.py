import pytest
from fastapi import status
from unittest.mock import Mock, patch
from app.models.prompt import Prompt


@pytest.mark.integration
class TestPromptIntegration:
    """Integration tests for prompt endpoints."""

    def test_create_and_get_prompt(self, client, test_user, sample_prompt_create_data):
        """Test creating a prompt and then retrieving it."""
        # Mock the AI service to avoid external API calls
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-api-key"}):
            with patch("google.generativeai.configure"):
                with patch("google.generativeai.GenerativeModel") as mock_model:
                    mock_instance = Mock()
                    mock_model.return_value = mock_instance
                    mock_instance.generate_content.return_value = Mock(text="Test response from AI")

                    # Create prompt
                    resp = client.post("/prompts/", json=sample_prompt_create_data)
                    assert resp.status_code == status.HTTP_201_CREATED
                    created = resp.json()

                    # Get the created prompt
                    get_resp = client.get(f"/prompts/{created['prompt_id']}")
                    assert get_resp.status_code == status.HTTP_200_OK
                    retrieved = get_resp.json()
                    assert retrieved["prompt_id"] == created["prompt_id"]
                    assert retrieved["user_id"] == test_user.telegram_id
                    assert retrieved["prompt_text"] == sample_prompt_create_data["prompt_text"]

    def test_get_user_prompts_empty(self, client, test_user):
        """Test getting prompts for a user with no prompts."""
        resp = client.get(f"/prompts/user/{test_user.telegram_id}")
        assert resp.status_code == status.HTTP_200_OK
        prompts = resp.json()
        assert isinstance(prompts, list)
        assert len(prompts) == 0

    def test_get_user_prompts_with_data(self, client, test_user, test_prompt):
        """Test getting prompts for a user with existing prompts."""
        resp = client.get(f"/prompts/user/{test_user.telegram_id}")
        assert resp.status_code == status.HTTP_200_OK
        prompts = resp.json()
        assert isinstance(prompts, list)
        assert len(prompts) == 1
        assert prompts[0]["prompt_id"] == test_prompt.prompt_id
        assert prompts[0]["user_id"] == test_user.telegram_id
        assert prompts[0]["prompt_text"] == test_prompt.prompt_text

    def test_get_user_prompts_multiple(self, client, test_user, test_prompt, session):
        """Test getting multiple prompts for a user."""
        # Create multiple prompts for the user
        prompt1 = Prompt(
            user_id=test_user.telegram_id,
            prompt_text="First prompt",
            response_text="First response",
            created_at=test_user.created_at
        )
        prompt2 = Prompt(
            user_id=test_user.telegram_id,
            prompt_text="Second prompt",
            response_text="Second response",
            created_at=test_user.created_at
        )
        session.add(prompt1)
        session.add(prompt2)
        session.commit()

        resp = client.get(f"/prompts/user/{test_user.telegram_id}")
        assert resp.status_code == status.HTTP_200_OK
        prompts = resp.json()
        assert isinstance(prompts, list)
        assert len(prompts) == 3  # 1 from test_prompt fixture + 2 new ones
        assert all(p["user_id"] == test_user.telegram_id for p in prompts)

    def test_get_user_prompts_different_user(self, client, test_user, test_prompt):
        """Test getting prompts for a different user returns empty list."""
        different_user_id = "999999999"
        resp = client.get(f"/prompts/user/{different_user_id}")
        assert resp.status_code == status.HTTP_200_OK
        prompts = resp.json()
        assert isinstance(prompts, list)
        assert len(prompts) == 0

    def test_get_prompt_not_found(self, client):
        """Test getting a non-existent prompt returns 404."""
        resp = client.get("/prompts/non-existent-id")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_update_prompt(self, client, test_prompt):
        """Test updating a prompt."""
        update_data = {
            "response_text": "Updated response",
            "completed_at": "2024-03-01T10:10:00"
        }
        resp = client.patch(f"/prompts/{test_prompt.prompt_id}", json=update_data)
        assert resp.status_code == status.HTTP_200_OK
        updated = resp.json()
        assert updated["response_text"] == "Updated response"

    def test_update_prompt_not_found(self, client):
        """Test updating a non-existent prompt returns 404."""
        update_data = {"response_text": "Updated response"}
        resp = client.patch("/prompts/non-existent-id", json=update_data)
        assert resp.status_code == status.HTTP_404_NOT_FOUND