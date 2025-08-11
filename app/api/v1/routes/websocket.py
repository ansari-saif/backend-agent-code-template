from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
import logging
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter()

# Dictionary to store active WebSocket connections
connections: Dict[str, WebSocket] = {}

@router.websocket("/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for one-way communication (send only).
    
    Args:
        websocket: WebSocket connection object
        user_id: Unique identifier for the user
    
    Features:
        - Accepts connections but doesn't process incoming messages
        - Maintains connection for potential future use
        - Handles connection lifecycle
    """
    await websocket.accept()
    connections[user_id] = websocket
    logger.info(f"User {user_id} connected to WebSocket (send-only mode)")
    
    try:
        # Keep connection alive without processing messages
        while True:
            # Just keep the connection open without receiving messages
            await websocket.receive_text()
            # Discard any received messages
            logger.debug(f"Discarded message from user {user_id}")
                
    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected from WebSocket")
    except Exception as e:
        logger.error(f"Error in WebSocket connection for user {user_id}: {str(e)}")
    finally:
        # Clean up connection
        if user_id in connections:
            del connections[user_id]
            logger.info(f"Cleaned up connection for user {user_id}")

@router.get("/status")
async def get_websocket_status():
    """
    Get WebSocket connection status and statistics.
    
    Returns:
        Dict containing connection count and status
    """
    return {
        "connected_users": len(connections),
        "status": "active",
        "active_user_ids": list(connections.keys())
    }

@router.post("/notification")
async def send_notification(notification_data: Dict[str, Any]):
    """
    Send a notification to all connected WebSocket users via HTTP endpoint.
    
    Args:
        notification_data: Dictionary containing notification information
            - message: The notification message (required)
    
    Returns:
        Dict containing notification status and sent count
    """
    if not connections:
        raise HTTPException(status_code=404, detail="No active WebSocket connections")
    
    # Prepare notification message with only message key
    notification = {
        "message": notification_data.get("message", "New notification")
    }
    
    # Send to all connected users
    sent_count = 0
    disconnected_users = []
    
    for user_id, websocket in connections.items():
        try:
            await websocket.send_text(json.dumps(notification))
            sent_count += 1
            logger.info(f"Notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {str(e)}")
            disconnected_users.append(user_id)
    
    # Clean up disconnected users
    for user_id in disconnected_users:
        if user_id in connections:
            del connections[user_id]
            logger.info(f"Removed disconnected user {user_id}")
    
    return {
        "status": "success",
        "message": f"Notification sent to {sent_count} users",
        "sent_count": sent_count,
        "total_connections": len(connections),
        "disconnected_users": len(disconnected_users)
    }
