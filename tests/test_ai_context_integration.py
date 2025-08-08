import pytest
from fastapi import status
from datetime import datetime

from app.models.ai_context import AIContext


@pytest.fixture
def sample_ai_context_data():
    return {
        "user_id": "test_user_123",
        "behavior_patterns": "{'morning_person': true}",
        "productivity_insights": "{'peak_hours': ['9-11', '15-17']}",
        "motivation_triggers": "{'rewards': ['completion', 'progress']}",
        "stress_indicators": "{'high_workload': true}",
        "optimal_work_times": "['morning', 'late_afternoon']"
    }


@pytest.mark.integration
def test_create_ai_context(client, sample_ai_context_data):
    response = client.post("/ai-context/", json=sample_ai_context_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    data = response.json()
    assert data["user_id"] == sample_ai_context_data["user_id"]
    assert data["behavior_patterns"] == sample_ai_context_data["behavior_patterns"]
    assert "context_id" in data
    assert "last_updated" in data


@pytest.mark.integration
def test_get_ai_context(client, session, sample_ai_context_data):
    # Create test data
    ai_context = AIContext(**sample_ai_context_data)
    session.add(ai_context)
    session.commit()
    
    response = client.get(f"/ai-context/{ai_context.context_id}")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["context_id"] == ai_context.context_id
    assert data["user_id"] == sample_ai_context_data["user_id"]


@pytest.mark.integration
def test_get_ai_context_by_user(client, session, sample_ai_context_data):
    # Create test data
    ai_context = AIContext(**sample_ai_context_data)
    session.add(ai_context)
    session.commit()
    
    response = client.get(f"/ai-context/user/{sample_ai_context_data['user_id']}")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["user_id"] == sample_ai_context_data["user_id"]
    assert data["context_id"] == ai_context.context_id


@pytest.mark.integration
def test_update_ai_context(client, session, sample_ai_context_data):
    # Create test data
    ai_context = AIContext(**sample_ai_context_data)
    session.add(ai_context)
    session.commit()
    
    update_data = {
        "behavior_patterns": "{'morning_person': false}",
        "productivity_insights": "{'peak_hours': ['10-12', '14-16']}"
    }
    
    response = client.put(f"/ai-context/{ai_context.context_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["behavior_patterns"] == update_data["behavior_patterns"]
    assert data["productivity_insights"] == update_data["productivity_insights"]
    assert data["motivation_triggers"] == sample_ai_context_data["motivation_triggers"]


@pytest.mark.integration
def test_delete_ai_context(client, session, sample_ai_context_data):
    # Create test data
    ai_context = AIContext(**sample_ai_context_data)
    session.add(ai_context)
    session.commit()
    
    response = client.delete(f"/ai-context/{ai_context.context_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify deletion
    get_response = client.get(f"/ai-context/{ai_context.context_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.integration
def test_get_nonexistent_ai_context(client):
    response = client.get("/ai-context/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.integration
def test_get_nonexistent_user_ai_context(client):
    response = client.get("/ai-context/user/nonexistent_user")
    assert response.status_code == status.HTTP_404_NOT_FOUND