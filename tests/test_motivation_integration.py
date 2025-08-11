import pytest
from unittest.mock import Mock, patch
from fastapi import status
from datetime import date, datetime, timedelta

from app.services.motivation_service import generate_motivation, get_motivation_stats
from app.models.task import Task, CompletionStatusEnum
from app.models.user import User
from app.models.ai_context import AIContext


@pytest.mark.integration
class TestMotivationService:
    """Test motivation service functionality."""
    
    async def test_generate_motivation_success(self, session, test_user, test_ai_context):
        """Test successful motivation generation."""
        with patch("app.services.ai_service.AIService") as mock_ai_service:
            mock_instance = Mock()
            mock_ai_service.return_value = mock_instance
            mock_instance.generate_motivation_message.return_value = "You're doing amazing! Keep pushing forward!"
            
            # Create some completed tasks
            completed_task = Task(
                user_id=test_user.telegram_id,
                description="Test completed task",
                completion_status=CompletionStatusEnum.COMPLETED,
                updated_at=datetime.now()
            )
            session.add(completed_task)
            session.commit()
            
            result = await generate_motivation(
                session=session,
                user_id=test_user.telegram_id,
                current_challenge="Feeling overwhelmed",
                stress_level=7
            )
            
            # Check that motivation text is generated and contains relevant content
            assert len(result["motivation_text"]) > 0
            assert "overwhelmed" in result["motivation_text"].lower() or "challenge" in result["motivation_text"].lower()
            assert result["current_challenge"] == "Feeling overwhelmed"
            assert result["stress_level"] == 7
            assert result["recent_achievements"] == 1
            assert result["user_phase"] == test_user.current_phase
    
    async def test_generate_motivation_user_not_found(self, session):
        """Test motivation generation with non-existent user."""
        with pytest.raises(ValueError, match="User invalid_user not found"):
            await generate_motivation(
                session=session,
                user_id="invalid_user",
                current_challenge="Test",
                stress_level=5
            )
    
    async def test_generate_motivation_ai_failure(self, session, test_user, test_ai_context):
        """Test motivation generation when AI fails."""
        with patch("app.services.ai_service.AIService") as mock_ai_service:
            mock_instance = Mock()
            mock_ai_service.return_value = mock_instance
            mock_instance.generate_motivation_message.side_effect = Exception("AI Error")
            
            result = await generate_motivation(
                session=session,
                user_id=test_user.telegram_id,
                current_challenge="Test challenge",
                stress_level=5
            )
            
            # Should return fallback motivation
            assert "entrepreneurial journey" in result["motivation_text"]
            assert result["error"] == "AI Error"
    
    def test_get_motivation_stats_success(self, session, test_user):
        """Test successful motivation stats retrieval."""
        # Create tasks for the last 30 days
        for i in range(5):
            task = Task(
                user_id=test_user.telegram_id,
                description=f"Task {i}",
                completion_status=CompletionStatusEnum.COMPLETED if i < 3 else CompletionStatusEnum.PENDING,
                created_at=datetime.now() - timedelta(days=i),
                updated_at=datetime.now() - timedelta(days=i) if i < 3 else None
            )
            session.add(task)
        session.commit()
        
        stats = get_motivation_stats(session=session, user_id=test_user.telegram_id)
        
        assert stats["total_tasks_30_days"] == 5
        assert stats["completed_tasks_30_days"] == 3
        assert stats["pending_tasks"] == 2
        assert stats["completion_rate_30_days"] == 60.0
        assert stats["user_phase"] == test_user.current_phase
    
    def test_get_motivation_stats_user_not_found(self, session):
        """Test motivation stats with non-existent user."""
        with pytest.raises(ValueError, match="User invalid_user not found"):
            get_motivation_stats(session=session, user_id="invalid_user")


@pytest.mark.integration
class TestMotivationAPI:
    """Test motivation API endpoints."""
    
    def test_generate_motivation_endpoint_success(self, client, test_user, test_ai_context):
        """Test successful motivation generation via API."""
        with patch("app.services.ai_service.AIService") as mock_ai_service:
            mock_instance = Mock()
            mock_ai_service.return_value = mock_instance
            mock_instance.generate_motivation_message.return_value = "You're doing amazing! Keep pushing forward!"
            
            request_data = {
                "user_id": test_user.telegram_id,
                "current_challenge": "Feeling overwhelmed",
                "stress_level": 7
            }
            
            response = client.post("/motivation/generate", json=request_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            # Check that motivation text is generated and contains relevant content
            assert len(data["motivation_text"]) > 0
            assert "overwhelmed" in data["motivation_text"].lower() or "challenge" in data["motivation_text"].lower()
            assert data["current_challenge"] == "Feeling overwhelmed"
            assert data["stress_level"] == 7
            assert data["user_id"] == test_user.telegram_id
    
    def test_generate_motivation_endpoint_user_not_found(self, client):
        """Test motivation generation with non-existent user via API."""
        request_data = {
            "user_id": "invalid_user",
            "current_challenge": "Test",
            "stress_level": 5
        }
        
        response = client.post("/motivation/generate", json=request_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
    
    def test_get_motivation_stats_endpoint_success(self, client, test_user, session):
        """Test successful motivation stats retrieval via API."""
        # Create some tasks
        from app.models.task import Task, CompletionStatusEnum
        from datetime import datetime, timedelta
        
        for i in range(3):
            task = Task(
                user_id=test_user.telegram_id,
                description=f"Task {i}",
                completion_status=CompletionStatusEnum.COMPLETED if i < 2 else CompletionStatusEnum.PENDING,
                created_at=datetime.now() - timedelta(days=i),
                updated_at=datetime.now() - timedelta(days=i) if i < 2 else None
            )
            session.add(task)
        session.commit()
        
        response = client.get(f"/motivation/stats/{test_user.telegram_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == test_user.telegram_id
        assert data["total_tasks_30_days"] == 3
        assert data["completed_tasks_30_days"] == 2
        assert data["pending_tasks"] == 1
        assert data["completion_rate_30_days"] == 66.7
    
    def test_get_motivation_stats_endpoint_user_not_found(self, client):
        """Test motivation stats with non-existent user via API."""
        response = client.get("/motivation/stats/invalid_user")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]


@pytest.mark.integration
class TestMotivationWebSocket:
    """Test motivation via WebSocket."""
    
    def test_websocket_motivation_request(self, client, test_user, test_ai_context):
        """Test motivation request via WebSocket."""
        with patch("app.services.ai_service.AIService") as mock_ai_service:
            mock_instance = Mock()
            mock_ai_service.return_value = mock_instance
            mock_instance.generate_motivation_message.return_value = "You're doing amazing! Keep pushing forward!"
            
            with client.websocket_connect(f"/api/v1/ws/{test_user.telegram_id}") as websocket:
                # Send motivation request
                motivation_request = {
                    "type": "motivation_requested",
                    "current_challenge": "Feeling overwhelmed",
                    "stress_level": 7
                }
                websocket.send_text(str(motivation_request).replace("'", '"'))
                
                # Receive response
                response = websocket.receive_text()
                response_data = eval(response.replace('null', 'None'))
                
                assert response_data["type"] == "motivation_generated"
                assert response_data["user_id"] == test_user.telegram_id
                assert response_data["motivation_text"] == "You're doing amazing! Keep pushing forward!"
                assert response_data["current_challenge"] == "Feeling overwhelmed"
                assert response_data["stress_level"] == 7
                assert "recent_achievements" in response_data
                assert "pending_tasks" in response_data
                assert "completion_rate" in response_data
                assert "user_phase" in response_data
