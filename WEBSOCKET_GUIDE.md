# WebSocket Integration Guide

## Overview

The Diary application provides a one-way WebSocket communication system for sending messages to connected users. The WebSocket endpoint accepts connections but doesn't process incoming messages - it's designed for server-to-client communication only.

## WebSocket Endpoint

**URL:** `ws://localhost:8000/api/v1/ws/{user_id}`

**Protocol:** WebSocket (ws:// or wss:// for secure connections)

**Mode:** Send-only (server to client)

## Connection

### Connect to WebSocket (Receive Only)

```javascript
// JavaScript/Node.js
const WebSocket = require('ws');

const user_id = "123456789";
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/${user_id}`);

ws.on('open', function open() {
    console.log('Connected to WebSocket (receive-only mode)');
});

ws.on('message', function message(data) {
    const response = JSON.parse(data);
    console.log('Received:', response);
});

ws.on('close', function close() {
    console.log('Disconnected from WebSocket');
});
```

```python
# Python
import asyncio
import websockets
import json

async def connect_websocket(user_id):
    uri = f"ws://localhost:8000/api/v1/ws/{user_id}"
    
    async with websockets.connect(uri) as websocket:
        print(f"Connected to WebSocket for user {user_id} (receive-only mode)")
        
        # Listen for messages from server
        async for message in websocket:
            response = json.loads(message)
            print(f"Received: {response}")

# Run the connection
asyncio.run(connect_websocket("123456789"))
```

## Sending Messages via HTTP Endpoints

### Send Notification

**POST** `/api/v1/ws/notification`

Send a simple notification to all connected users:

```json
{
  "message": "Server maintenance scheduled for tomorrow"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Notification sent to 3 users",
  "sent_count": 3,
  "total_connections": 3,
  "disconnected_users": 0
}
```

**What gets sent to WebSocket clients:**
```json
{
  "message": "Server maintenance scheduled for tomorrow"
}
```

## WebSocket Status Endpoint

**GET** `/api/v1/ws/status`

Returns the current WebSocket connection status:

```json
{
  "connected_users": 5,
  "status": "active",
  "active_user_ids": ["123456789", "987654321", "555666777"]
}
```

## Complete JavaScript Client Example (Receive Only)

```javascript
class DiaryWebSocketClient {
    constructor(userId, baseUrl = 'ws://localhost:8000') {
        this.userId = userId;
        this.baseUrl = baseUrl;
        this.ws = null;
        this.isConnected = false;
        this.messageHandlers = new Map();
    }

    connect() {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(`${this.baseUrl}/api/v1/ws/${this.userId}`);
            
            this.ws.onopen = () => {
                this.isConnected = true;
                console.log('WebSocket connected (receive-only mode)');
                resolve();
            };
            
            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            };
            
            this.ws.onclose = () => {
                this.isConnected = false;
                console.log('WebSocket disconnected');
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };
        });
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
            this.isConnected = false;
        }
    }

    handleMessage(message) {
        const handler = this.messageHandlers.get(message.type);
        if (handler) {
            handler(message);
        } else {
            console.log('Received message:', message);
        }
    }

    onMessage(type, handler) {
        this.messageHandlers.set(type, handler);
    }

    onNotification(handler) {
        this.onMessage('notification', handler);
    }


}

// Usage Example
async function main() {
    const client = new DiaryWebSocketClient('123456789');
    
    // Set up message handlers
    client.onNotification((message) => {
        console.log('Notification received:', message.message);
    });
    

    
    try {
        // Connect to WebSocket
        await client.connect();
        
        // Keep connection alive for 30 seconds
        setTimeout(() => {
            client.disconnect();
        }, 30000);
        
    } catch (error) {
        console.error('Error:', error);
    }
}

main();
```

## Python Client Example (Receive Only)

```python
import asyncio
import websockets
import json
from typing import Dict, Callable, Any

class DiaryWebSocketClient:
    def __init__(self, user_id: str, base_url: str = "ws://localhost:8000"):
        self.user_id = user_id
        self.base_url = base_url
        self.websocket = None
        self.message_handlers: Dict[str, Callable] = {}
    
    async def connect(self):
        """Connect to WebSocket"""
        uri = f"{self.base_url}/api/v1/ws/{self.user_id}"
        self.websocket = await websockets.connect(uri)
        print(f"Connected to WebSocket for user {self.user_id} (receive-only mode)")
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
    
    def on_message(self, message_type: str, handler: Callable):
        """Register message handler"""
        self.message_handlers[message_type] = handler
    
    async def listen(self):
        """Listen for incoming messages"""
        if not self.websocket:
            raise Exception("WebSocket not connected")
        
        async for message in self.websocket:
            data = json.loads(message)
            message_type = data.get("type", "unknown")
            
            if message_type in self.message_handlers:
                self.message_handlers[message_type](data)
            else:
                print(f"Received message: {data}")
    
    async def run(self, duration: int = 30):
        """Run the client for a specified duration"""
        try:
            await self.connect()
            
            # Listen for messages
            await asyncio.wait_for(self.listen(), timeout=duration)
            
        except asyncio.TimeoutError:
            print("Connection timeout")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await self.disconnect()

# Usage Example
async def main():
    client = DiaryWebSocketClient("123456789")
    
    # Set up message handlers
    def on_notification(message):
        print(f"Notification: {message['message']}")
    

    
    client.on_message("notification", on_notification)

    
    # Run client for 30 seconds
    await client.run(30)

# Run the example
if __name__ == "__main__":
    asyncio.run(main())
```

## Error Handling

### Connection Errors
- **Connection Refused**: Server not running or wrong URL
- **Authentication**: User ID validation (if implemented)
- **Network Issues**: Handle reconnection logic

### Server Errors
- **No Active Connections**: 404 error when no users are connected
- **Message Send Failures**: Automatic cleanup of disconnected users

## Troubleshooting

### Common Issues

1. **404 Error**: Make sure the server is running and the WebSocket router is properly mounted
2. **Connection Refused**: Check if the server is running on the correct port (8000)
3. **Import Errors**: Install required dependencies:
   ```bash
   pip install websockets  # For Python
   npm install ws          # For Node.js
   ```

### Testing Connection

```bash
# Test status endpoint
curl http://localhost:8000/api/v1/ws/status

# Test WebSocket with wscat (receive-only)
wscat -c ws://localhost:8000/api/v1/ws/123456789

# Send notification via HTTP endpoint
curl -X POST http://localhost:8000/api/v1/ws/notification \
  -H "Content-Type: application/json" \
  -d '{"message": "Test notification"}'
```

## Best Practices

1. **Reconnection Logic**: Implement automatic reconnection on disconnect
2. **Error Handling**: Handle connection and message errors gracefully
3. **Resource Cleanup**: Properly close connections when done
4. **Message Validation**: Validate message format before sending via HTTP
5. **Rate Limiting**: Implement rate limiting for HTTP message sending

## Security Considerations

- **User Authentication**: Validate user_id on connection
- **Message Validation**: Sanitize incoming messages via HTTP endpoints
- **Rate Limiting**: Implement rate limiting for HTTP message sending
- **Connection Limits**: Limit number of connections per user

## Testing

### Test Status Endpoint
```bash
curl http://localhost:8000/api/v1/ws/status
```

### Test Notification Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/ws/notification \
  -H "Content-Type: application/json" \
  -d '{"message": "Test notification"}'
```

## Integration with Task Management

The WebSocket can be used to send real-time updates for:

- Task completion notifications
- Goal progress updates
- AI-generated motivation messages
- System announcements and alerts
- Real-time collaboration features
- Progress tracking updates

## Example Use Cases

1. **System Notifications**: Broadcast important announcements to all users
2. **Task Updates**: Send notifications when tasks are completed
3. **Progress Tracking**: Real-time progress updates
4. **AI Integration**: Send AI-generated insights and recommendations
5. **Maintenance Alerts**: Notify users about system maintenance
6. **Feature Announcements**: Announce new features or updates

## Message Types

The system supports notifications sent via the `/notification` endpoint:

- **notification**: Simple notifications with just a message
