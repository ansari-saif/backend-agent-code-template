from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlmodel import Session
import json
import logging

from app.core.database import get_session
from app.services.motivation_service import generate_motivation

logger = logging.getLogger(__name__)
router = APIRouter()

# Simple dictionary to store connections
connections = {}

@router.websocket("/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Simple WebSocket endpoint"""
    await websocket.accept()
    connections[user_id] = websocket
    logger.info(f"User {user_id} connected")
    
    # Get database session
    session = next(get_session())
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                response = {
                    "type": "pong",
                    "user_id": user_id,
                    "message": "Pong!"
                }
                await websocket.send_text(json.dumps(response))
                
            elif message.get("type") == "motivation_requested":
                # Generate actual motivation using AI service
                try:
                    motivation_data = await generate_motivation(
                        session=session,
                        user_id=user_id,
                        current_challenge=message.get("current_challenge", ""),
                        stress_level=message.get("stress_level", 5)
                    )
                    
                    response = {
                        "type": "motivation_generated",
                        "user_id": user_id,
                        "motivation_text": motivation_data["motivation_text"],
                        "current_challenge": motivation_data["current_challenge"],
                        "stress_level": motivation_data["stress_level"],
                        "recent_achievements": motivation_data["recent_achievements"],
                        "pending_tasks": motivation_data["pending_tasks"],
                        "completion_rate": motivation_data["completion_rate"],
                        "user_phase": motivation_data["user_phase"],
                        "days_until_target": motivation_data["days_until_target"]
                    }
                except Exception as e:
                    logger.error(f"Error generating motivation for user {user_id}: {e}")
                    # Fallback response
                    response = {
                        "type": "motivation_generated",
                        "user_id": user_id,
                        "motivation_text": "You're doing great! Keep pushing forward! 💪",
                        "current_challenge": message.get("current_challenge", ""),
                        "stress_level": message.get("stress_level", 5),
                        "recent_achievements": 0,
                        "pending_tasks": 0,
                        "completion_rate": 0,
                        "user_phase": "Unknown",
                        "days_until_target": None
                    }
                
                await websocket.send_text(json.dumps(response))
                
            else:
                # Echo back any other message
                response = {
                    "type": "echo",
                    "user_id": user_id,
                    "message": f"Received: {message}"
                }
                await websocket.send_text(json.dumps(response))
                
    except WebSocketDisconnect:
        if user_id in connections:
            del connections[user_id]
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        if user_id in connections:
            del connections[user_id]
    finally:
        session.close()

@router.get("/status")
async def get_websocket_status():
    """Get simple WebSocket status"""
    return {
        "connected_users": len(connections),
        "status": "active"
    }
