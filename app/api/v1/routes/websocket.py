from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
import logging
import json
from typing import Dict, Any
from datetime import datetime
from sqlmodel import Session

from app.core.database import get_session
from app.services.prompt_service import PromptService
from app.schemas.prompt import PromptCreate

logger = logging.getLogger(__name__)
router = APIRouter()

# Dictionary to store active WebSocket connections
connections: Dict[str, WebSocket] = {}

async def handle_chat_message(websocket: WebSocket, user_id: str, message: Dict[str, Any]):
    """Handle chat messages - broadcast to other users"""
    # Broadcast message to other connected users
    chat_message = {
        "type": "chat",
        "user_id": user_id,
        "message": message.get("message", ""),
        "timestamp": message.get("timestamp")
    }
    
    # Send to all connected users (including sender for confirmation)
    logger.info(f"Broadcasting to {len(connections)} connected users: {list(connections.keys())}")
    for other_user_id, other_websocket in connections.items():
        try:
            await other_websocket.send_text(json.dumps(chat_message))
            logger.info(f"Chat message sent to user {other_user_id}")
        except Exception as e:
            logger.error(f"Failed to send chat message to user {other_user_id}: {str(e)}")

async def handle_prompt_message(websocket: WebSocket, user_id: str, message: Dict[str, Any], prompt_service: PromptService):
    """Handle prompt messages - create and process with AI"""
    # Validate required fields
    if "message" not in message:
        error_response = {
            "type": "error",
            "message": "Missing required field: message"
        }
        await websocket.send_text(json.dumps(error_response))
        return
    
    # Create prompt data
    prompt_data = PromptCreate(
        user_id=user_id,
        prompt_text=message["message"]
    )
    
    # Get database session
    session = next(get_session())
    
    try:
        # First create the prompt
        prompt = await prompt_service.create_prompt(session, prompt_data)
        logger.info(f"Created prompt {prompt.prompt_id} for user {user_id}")
        
        # Then process it with Gemini
        processed_prompt = await prompt_service.process_prompt(session, prompt)
        logger.info(f"Processed prompt {prompt.prompt_id} for user {user_id}")
        
        # Send the processed response
        success_response = {
            "message": processed_prompt.response_text
        }
        await websocket.send_text(json.dumps(success_response))
        
    except ValueError as e:
        error_response = {
            "type": "error",
            "message": f"Processing error: {str(e)}"
        }
        await websocket.send_text(json.dumps(error_response))
        logger.error(f"Error processing prompt for user {user_id}: {str(e)}")
    
    finally:
        session.close()

@router.websocket("/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for two-way communication (chat and prompt support).
    
    Args:
        websocket: WebSocket connection object
        user_id: Unique identifier for the user
    
    Features:
        - Accepts connections and processes incoming messages
        - Handles chat messages (broadcasts to other users)
        - Handles prompt messages (creates and processes with AI)
        - Handles connection lifecycle
    """
    await websocket.accept()
    connections[user_id] = websocket
    logger.info(f"User {user_id} connected to WebSocket (chat + prompt mode)")
    
    # Initialize prompt service
    prompt_service = PromptService()
    
    try:
        # Process incoming messages for chat and prompts
        while True:
            message_data = await websocket.receive_text()
            logger.info(f"Raw message received from user {user_id}: {message_data}")
            
            try:
                message = json.loads(message_data)
                logger.info(f"Parsed message from user {user_id}: {message}")
                await handle_prompt_message(websocket, user_id, message, prompt_service)
               
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from user {user_id}: {message_data}")
                # Send error message back to sender
                error_message = {
                    "type": "error",
                    "message": "Invalid message format. Please send valid JSON."
                }
                await websocket.send_text(json.dumps(error_message))
                
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
async def send_notification(notification_data: Dict[str, Any], session: Session = Depends(get_session)):
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
    notification_message = notification_data.get("message", "New notification")
    notification = {
        "message": notification_message
    }
    
    # Send to all connected users
    sent_count = 0
    disconnected_users = []
    
    for user_id, websocket in connections.items():
        try:
            await websocket.send_text(json.dumps(notification))
            sent_count += 1
            logger.info(f"Notification sent to user {user_id}")
            
            # Store notification as prompt record for each user
            try:
                from app.models.prompt import Prompt
                prompt = Prompt(
                    user_id=user_id,
                    prompt_text=f"System notification: {notification_message}",
                    response_text=notification_message,
                    completed_at=datetime.now()
                )
                session.add(prompt)
                session.commit()
                session.refresh(prompt)
                logger.info(f"Stored notification as prompt record for user {user_id}")
                
            except Exception as e:
                logger.error(f"Failed to store notification as prompt for user {user_id}: {str(e)}")
                
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
