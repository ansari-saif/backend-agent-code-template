import os
import pytest
from unittest.mock import Mock, patch
from fastapi import status
from datetime import datetime

from app.models.prompt import Prompt
from app.services.prompt_service import PromptService

@pytest.fixture(autouse=True)
def setup_test_env():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        yield

@pytest.fixture
def sample_prompt_data():
    return {
        "user_id": "test-user-123",
        "prompt_text": "What is the meaning of life?"
    }

@pytest.fixture
def sample_prompt_response():
    return "The meaning of life is 42."

def test_create_prompt(client, session, sample_prompt_data, sample_prompt_response):
    with patch("app.services.prompt_service.genai") as mock_genai:
        # Setup mock
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_model.generate_content = Mock()
        mock_model.generate_content.return_value = Mock(text=sample_prompt_response)
        
        # Make request
        response = client.post("/prompts/", json=sample_prompt_data)
        
        # Print response for debugging
        print(f"Response: {response.status_code} - {response.json()}")
        
        # Assert response
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == sample_prompt_data["user_id"]
        assert data["prompt_text"] == sample_prompt_data["prompt_text"]
        assert data["response_text"] == sample_prompt_response
        assert "prompt_id" in data
        assert "created_at" in data
        assert "completed_at" in data

def test_get_prompt(client, session, sample_prompt_data):
    # Create a prompt first
    prompt = Prompt(**sample_prompt_data, response_text="Test response")
    session.add(prompt)
    session.commit()
    
    # Get the prompt
    response = client.get(f"/prompts/{prompt.prompt_id}")
    
    # Assert response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["prompt_id"] == prompt.prompt_id
    assert data["user_id"] == sample_prompt_data["user_id"]
    assert data["prompt_text"] == sample_prompt_data["prompt_text"]
    assert data["response_text"] == "Test response"

def test_get_nonexistent_prompt(client):
    response = client.get("/prompts/nonexistent-id")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_prompt(client, session, sample_prompt_data):
    # Create a prompt first
    prompt = Prompt(**sample_prompt_data)
    session.add(prompt)
    session.commit()
    
    # Update data
    update_data = {
        "response_text": "Updated response",
        "completed_at": datetime.utcnow().isoformat()
    }
    
    # Update the prompt
    response = client.patch(f"/prompts/{prompt.prompt_id}", json=update_data)
    
    # Assert response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["response_text"] == update_data["response_text"]

def test_gemini_api_error(client, session):
    # Create a prompt that will trigger an error
    error_prompt_data = {
        "user_id": "test-user-123",
        "prompt_text": "This should trigger an error"
    }
    
    # Make request
    response = client.post("/prompts/", json=error_prompt_data)
    
    # Assert response
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Failed to process prompt" in response.json()["detail"]