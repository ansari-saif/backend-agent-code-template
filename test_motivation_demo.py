#!/usr/bin/env python3
"""
Demo script to test the motivation system.
This script demonstrates how to use the motivation API endpoints.
"""

import requests
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_motivation_generation():
    """Test motivation generation endpoint."""
    print("=== Testing Motivation Generation ===")
    
    # Test data
    motivation_request = {
        "user_id": "123456789",  # Use the test user ID
        "current_challenge": "Feeling overwhelmed with MVP development",
        "stress_level": 7
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/motivation/generate",
            json=motivation_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Motivation generated successfully!")
            print(f"📝 Motivation: {data['motivation_text']}")
            print(f"🎯 Current Challenge: {data['current_challenge']}")
            print(f"😰 Stress Level: {data['stress_level']}")
            print(f"🏆 Recent Achievements: {data['recent_achievements']}")
            print(f"📋 Pending Tasks: {data['pending_tasks']}")
            print(f"📊 Completion Rate: {data['completion_rate']}%")
            print(f"🚀 User Phase: {data['user_phase']}")
            if data['days_until_target']:
                print(f"⏰ Days until target: {data['days_until_target']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_motivation_stats():
    """Test motivation stats endpoint."""
    print("\n=== Testing Motivation Stats ===")
    
    try:
        response = requests.get(f"{BASE_URL}/motivation/stats/123456789")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Motivation stats retrieved successfully!")
            print(f"📊 Total tasks (30 days): {data['total_tasks_30_days']}")
            print(f"✅ Completed tasks (30 days): {data['completed_tasks_30_days']}")
            print(f"📋 Pending tasks: {data['pending_tasks']}")
            print(f"📈 Completion rate (30 days): {data['completion_rate_30_days']}%")
            print(f"🔥 Current streak: {data['current_streak_days']} days")
            print(f"🚀 User phase: {data['user_phase']}")
            if data['days_until_target']:
                print(f"⏰ Days until target: {data['days_until_target']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_websocket_motivation():
    """Test WebSocket motivation (requires websocket client)."""
    print("\n=== WebSocket Motivation Test ===")
    print("ℹ️  To test WebSocket motivation, use the simple_websocket_test.html file")
    print("   or connect to ws://localhost:8000/api/v1/ws/123456789")
    print("   and send: {\"type\": \"motivation_requested\", \"current_challenge\": \"Test\", \"stress_level\": 5}")


if __name__ == "__main__":
    print("🎯 Motivation System Demo")
    print("=" * 50)
    
    test_motivation_generation()
    test_motivation_stats()
    test_websocket_motivation()
    
    print("\n" + "=" * 50)
    print("✨ Demo completed!")
    print("\nTo run the server:")
    print("1. Activate virtual environment: source venv/bin/activate")
    print("2. Start server: python -m uvicorn app.main:app --reload")
    print("3. Open API docs: http://localhost:8000/docs")
