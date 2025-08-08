import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from datetime import datetime, timedelta, date
from dateutil.parser import parse

from app.main import app
from app.models.user import User
from app.models.day_log import DayLog
from app.core.database import get_session


class TestDayLogIntegration:
    """Integration tests for DayLog functionality."""

    def test_day_log_lifecycle(self, client, session: Session, test_user, sample_day_log_create_data):
        """Test complete day log lifecycle: create, read, update, delete."""
        
        # 1. Create a new day log
        response = client.post("/day-logs/", json=sample_day_log_create_data)
        assert response.status_code == 201
        created_log = response.json()
        assert created_log["summary"] == sample_day_log_create_data["summary"]
        assert created_log["user_id"] == test_user.telegram_id
        log_id = created_log["log_id"]

        # 2. Read the created day log
        response = client.get(f"/day-logs/{log_id}")
        assert response.status_code == 200
        retrieved_log = response.json()
        assert retrieved_log == created_log

        # 3. Update the day log
        update_data = {
            "summary": "Updated summary",
            "highlights": "New achievement unlocked",
            "challenges": "Faced and overcame new obstacles"
        }
        response = client.patch(f"/day-logs/{log_id}", json=update_data)
        assert response.status_code == 200
        updated_log = response.json()
        assert updated_log["summary"] == update_data["summary"]
        assert updated_log["highlights"] == update_data["highlights"]
        assert updated_log["challenges"] == update_data["challenges"]

        # 4. Delete the day log
        response = client.delete(f"/day-logs/{log_id}")
        assert response.status_code == 204

        # Verify deletion
        response = client.get(f"/day-logs/{log_id}")
        assert response.status_code == 404

    def test_get_user_day_logs(self, client, session: Session, test_user):
        """Test getting all day logs for a user."""
        
        # Create multiple day logs for the user
        current_time = datetime.now()
        logs_data = [
            {
                "user_id": test_user.telegram_id,
                "date": date.today().isoformat(),
                "start_time": current_time.isoformat(),
                "end_time": (current_time + timedelta(hours=8)).isoformat(),
                "summary": f"Day log {i}",
                "highlights": f"Highlight {i}",
                "challenges": f"Challenge {i}"
            }
            for i in range(3)
        ]

        created_logs = []
        for log_data in logs_data:
            response = client.post("/day-logs/", json=log_data)
            assert response.status_code == 201
            created_logs.append(response.json())

        # Test getting all user logs
        response = client.get(f"/day-logs/user/{test_user.telegram_id}")
        assert response.status_code == 200
        user_logs = response.json()
        assert len(user_logs) == 3

        # Test pagination
        response = client.get(
            f"/day-logs/user/{test_user.telegram_id}",
            params={"skip": 1, "limit": 1}
        )
        assert response.status_code == 200
        paginated_logs = response.json()
        assert len(paginated_logs) == 1
        assert paginated_logs[0]["summary"] == "Day log 1"

    def test_get_user_day_log_by_date(self, client, session: Session, test_user):
        """Test getting a user's day log by specific date."""
        
        # Create day logs for different dates
        current_time = datetime.now()
        dates = [
            date.today(),
            date.today() - timedelta(days=1),
            date.today() - timedelta(days=2)
        ]

        for i, log_date in enumerate(dates):
            log_data = {
                "user_id": test_user.telegram_id,
                "date": log_date.isoformat(),
                "start_time": current_time.isoformat(),
                "end_time": (current_time + timedelta(hours=8)).isoformat(),
                "summary": f"Day log for {log_date}",
                "highlights": f"Highlight {i}",
                "challenges": f"Challenge {i}"
            }
            response = client.post("/day-logs/", json=log_data)
            assert response.status_code == 201

        # Test getting log for specific date
        response = client.get(
            f"/day-logs/user/{test_user.telegram_id}/date/{date.today().isoformat()}"
        )
        assert response.status_code == 200
        day_log = response.json()
        assert day_log["date"] == date.today().isoformat()
        assert day_log["summary"] == f"Day log for {date.today()}"

        # Test getting log for non-existent date
        future_date = date.today() + timedelta(days=7)
        response = client.get(
            f"/day-logs/user/{test_user.telegram_id}/date/{future_date.isoformat()}"
        )
        assert response.status_code == 404

    def test_day_log_validation(self, client, session: Session, test_user):
        """Test day log validation rules."""
        
        current_time = datetime.now()
        
        # Test invalid user
        invalid_log = {
            "user_id": "non_existent_user",
            "date": date.today().isoformat(),
            "start_time": current_time.isoformat(),
            "summary": "Test log"
        }
        response = client.post("/day-logs/", json=invalid_log)
        assert response.status_code == 404

        # Test invalid date format
        invalid_date_log = {
            "user_id": test_user.telegram_id,
            "date": "invalid-date",
            "start_time": current_time.isoformat(),
            "summary": "Test log"
        }
        response = client.post("/day-logs/", json=invalid_date_log)
        assert response.status_code == 422

        # Test end_time before start_time
        invalid_time_log = {
            "user_id": test_user.telegram_id,
            "date": date.today().isoformat(),
            "start_time": current_time.isoformat(),
            "end_time": (current_time - timedelta(hours=1)).isoformat(),
            "summary": "Test log"
        }
        response = client.post("/day-logs/", json=invalid_time_log)
        assert response.status_code == 422

    def test_user_day_log_relationship(self, client, session: Session, test_user):
        """Test relationship between User and DayLog models."""
        
        # Create multiple day logs for the user
        current_time = datetime.now()
        logs_data = [
            {
                "user_id": test_user.telegram_id,
                "date": date.today().isoformat(),
                "start_time": current_time.isoformat(),
                "end_time": (current_time + timedelta(hours=8)).isoformat(),
                "summary": f"Day log {i}"
            }
            for i in range(3)
        ]

        for log_data in logs_data:
            response = client.post("/day-logs/", json=log_data)
            assert response.status_code == 201

        # Query user and check day_logs relationship
        user = session.get(User, test_user.telegram_id)
        assert len(user.day_logs) == 3
        assert all(isinstance(log, DayLog) for log in user.day_logs)
        assert all(log.user_id == test_user.telegram_id for log in user.day_logs)

        # Delete a day log and verify user relationship is updated
        log_to_delete = user.day_logs[0]
        response = client.delete(f"/day-logs/{log_to_delete.log_id}")
        assert response.status_code == 204

        session.refresh(user)
        assert len(user.day_logs) == 2

    def test_day_log_bulk_operations(self, client, session: Session, test_user):
        """Test bulk operations and complex filtering for day logs."""
        
        # Create day logs for multiple days with different attributes
        current_time = datetime.now()
        test_days = 5
        logs_data = []
        
        for i in range(test_days):
            log_date = date.today() - timedelta(days=i)
            log_data = {
                "user_id": test_user.telegram_id,
                "date": log_date.isoformat(),
                "start_time": current_time.isoformat(),
                "end_time": (current_time + timedelta(hours=8)).isoformat(),
                "summary": f"Day {i} summary",
                "highlights": f"Day {i} highlights",
                "challenges": f"Day {i} challenges",
                "learnings": f"Day {i} learnings",
                "gratitude": f"Day {i} gratitude",
                "tomorrow_plan": f"Day {i} plan",
                "weather": "Sunny" if i % 2 == 0 else "Rainy",
                "location": "Home" if i % 2 == 0 else "Office"
            }
            logs_data.append(log_data)
            response = client.post("/day-logs/", json=log_data)
            assert response.status_code == 201

        # Test filtering by date range
        start_date = (date.today() - timedelta(days=3)).isoformat()
        end_date = date.today().isoformat()
        response = client.get(
            f"/day-logs/user/{test_user.telegram_id}/range",
            params={"start_date": start_date, "end_date": end_date}
        )
        assert response.status_code == 200
        date_range_logs = response.json()
        assert len(date_range_logs) == 4  # Today + 3 days back

        # Test filtering by location
        response = client.get(
            f"/day-logs/user/{test_user.telegram_id}",
            params={"location": "Home"}
        )
        assert response.status_code == 200
        home_logs = response.json()
        assert len(home_logs) == 3  # Days with even indices (0, 2, 4)
        assert all(log["location"] == "Home" for log in home_logs)

        # Test filtering by weather
        response = client.get(
            f"/day-logs/user/{test_user.telegram_id}",
            params={"weather": "Rainy"}
        )
        assert response.status_code == 200
        rainy_logs = response.json()
        assert len(rainy_logs) == 2  # Days with odd indices (1, 3)
        assert all(log["weather"] == "Rainy" for log in rainy_logs)

        # Test complex filtering (location + date range)
        response = client.get(
            f"/day-logs/user/{test_user.telegram_id}/range",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "location": "Home"
            }
        )
        assert response.status_code == 200
        filtered_logs = response.json()
        assert all(
            log["location"] == "Home" and
            parse(log["date"]) >= parse(start_date) and
            parse(log["date"]) <= parse(end_date)
            for log in filtered_logs
        )

    def test_day_log_statistics(self, client, session: Session, test_user):
        """Test day log statistics and aggregations."""
        
        # Create day logs with varying durations
        current_time = datetime.now()
        durations = [4, 6, 8, 10, 12]  # hours
        
        for i, duration in enumerate(durations):
            log_data = {
                "user_id": test_user.telegram_id,
                "date": (date.today() - timedelta(days=i)).isoformat(),
                "start_time": current_time.isoformat(),
                "end_time": (current_time + timedelta(hours=duration)).isoformat(),
                "summary": f"Day log with {duration}h duration"
            }
            response = client.post("/day-logs/", json=log_data)
            assert response.status_code == 201

        # Test average duration statistics
        response = client.get(f"/day-logs/user/{test_user.telegram_id}/stats")
        assert response.status_code == 200
        stats = response.json()
        
        assert "average_duration" in stats
        assert "total_logs" in stats
        assert "locations_summary" in stats
        assert "weather_summary" in stats
        
        assert stats["total_logs"] == len(durations)
        assert abs(stats["average_duration"] - sum(durations)/len(durations)) < 0.1

    def test_day_log_concurrent_updates(self, client, session: Session, test_user):
        """Test handling of concurrent updates to day logs."""
        
        # Create initial day log
        current_time = datetime.now()
        initial_data = {
            "user_id": test_user.telegram_id,
            "date": date.today().isoformat(),
            "start_time": current_time.isoformat(),
            "summary": "Initial summary"
        }
        response = client.post("/day-logs/", json=initial_data)
        assert response.status_code == 201
        log_id = response.json()["log_id"]

        # Simulate concurrent updates
        update_1 = {
            "summary": "Update 1",
            "highlights": "Highlight 1"
        }
        update_2 = {
            "summary": "Update 2",
            "challenges": "Challenge 2"
        }

        # Make updates in quick succession
        response1 = client.patch(f"/day-logs/{log_id}", json=update_1)
        response2 = client.patch(f"/day-logs/{log_id}", json=update_2)

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Verify final state
        response = client.get(f"/day-logs/{log_id}")
        assert response.status_code == 200
        final_state = response.json()

        # The last update should win for conflicting fields
        assert final_state["summary"] == "Update 2"
        # Non-conflicting fields from both updates should be preserved
        assert final_state["highlights"] == "Highlight 1"
        assert final_state["challenges"] == "Challenge 2"

    def test_day_log_edge_cases(self, client, session: Session, test_user):
        """Test edge cases and boundary conditions."""
        
        current_time = datetime.now()

        # Test extremely long text fields
        long_text = "A" * 5000  # 5000 characters
        long_text_log = {
            "user_id": test_user.telegram_id,
            "date": date.today().isoformat(),
            "start_time": current_time.isoformat(),
            "summary": long_text,
            "highlights": long_text,
            "challenges": long_text
        }
        response = client.post("/day-logs/", json=long_text_log)
        assert response.status_code == 422  # Should reject too long text

        # Test missing required fields
        incomplete_log = {
            "user_id": test_user.telegram_id,
            "summary": "Test log"
        }
        response = client.post("/day-logs/", json=incomplete_log)
        assert response.status_code == 422

        # Test invalid time formats
        invalid_time_log = {
            "user_id": test_user.telegram_id,
            "date": date.today().isoformat(),
            "start_time": "invalid_time",
            "summary": "Test log"
        }
        response = client.post("/day-logs/", json=invalid_time_log)
        assert response.status_code == 422

        # Test update with empty fields
        valid_log = {
            "user_id": test_user.telegram_id,
            "date": date.today().isoformat(),
            "start_time": current_time.isoformat(),
            "summary": "Initial summary"
        }
        response = client.post("/day-logs/", json=valid_log)
        assert response.status_code == 201
        log_id = response.json()["log_id"]

        empty_update = {
            "summary": "",
            "highlights": "",
            "challenges": ""
        }
        response = client.patch(f"/day-logs/{log_id}", json=empty_update)
        assert response.status_code == 200
        updated_log = response.json()
        assert updated_log["summary"] == ""  # Should allow empty strings
        assert updated_log["highlights"] == ""
        assert updated_log["challenges"] == ""