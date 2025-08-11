# WebSocket Integration Guide

## Overview

The Diary application provides real-time WebSocket communication for instant updates, motivation messages, and interactive features. The WebSocket endpoint supports user-specific connections and handles various message types.

## WebSocket Endpoint

**URL:** `ws://localhost:8000/api/v1/ws/{user_id}`

**Protocol:** WebSocket (ws:// or wss:// for secure connections)

## Connection

### Connect to WebSocket

```javascript
// JavaScript/Node.js
const WebSocket = require('ws');

const user_id = "123456789";
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/${user_id}`);

ws.on('open', function open() {
    console.log('Connected to WebSocket');
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
        print(f"Connected to WebSocket for user {user_id}")
        
        # Send a ping message
        ping_message = {"type": "ping"}
        await websocket.send(json.dumps(ping_message))
        
        # Listen for messages
        async for message in websocket:
            response = json.loads(message)
            print(f"Received: {response}")

# Run the connection
asyncio.run(connect_websocket("123456789"))
```

## Message Types

### 1. Ping/Pong

**Send:**
```json
{
  "type": "ping"
}
```

**Receive:**
```json
{
  "type": "pong",
  "user_id": "123456789",
  "message": "Pong!"
}
```

### 2. Motivation Request

**Send:**
```json
{
  "type": "motivation_requested",
  "current_challenge": "Working on a difficult feature",
  "stress_level": 7
}
```

**Receive:**
```json
{
  "type": "motivation_generated",
  "user_id": "123456789",
  "motivation_text": "You're doing great! Keep pushing forward! 💪",
  "current_challenge": "Working on a difficult feature",
  "stress_level": 7
}
```

### 3. Echo (Default)

**Send:**
```json
{
  "type": "custom_message",
  "data": "Any custom data"
}
```

**Receive:**
```json
{
  "type": "echo",
  "user_id": "123456789",
  "message": "Received: {\"type\": \"custom_message\", \"data\": \"Any custom data\"}"
}
```

## Complete JavaScript Client Example

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
                console.log('WebSocket connected');
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

    sendMessage(message) {
        if (!this.isConnected) {
            throw new Error('WebSocket not connected');
        }
        this.ws.send(JSON.stringify(message));
    }

    ping() {
        this.sendMessage({ type: 'ping' });
    }

    requestMotivation(currentChallenge = '', stressLevel = 5) {
        this.sendMessage({
            type: 'motivation_requested',
            current_challenge: currentChallenge,
            stress_level: stressLevel
        });
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

    onPong(handler) {
        this.onMessage('pong', handler);
    }

    onMotivation(handler) {
        this.onMessage('motivation_generated', handler);
    }

    onEcho(handler) {
        this.onMessage('echo', handler);
    }
}

// Usage Example
async function main() {
    const client = new DiaryWebSocketClient('123456789');
    
    // Set up message handlers
    client.onPong((message) => {
        console.log('Pong received:', message.message);
    });
    
    client.onMotivation((message) => {
        console.log('Motivation:', message.motivation_text);
        console.log('Challenge:', message.current_challenge);
        console.log('Stress Level:', message.stress_level);
    });
    
    client.onEcho((message) => {
        console.log('Echo:', message.message);
    });
    
    try {
        // Connect to WebSocket
        await client.connect();
        
        // Send ping
        client.ping();
        
        // Request motivation
        client.requestMotivation('Working on API documentation', 6);
        
        // Send custom message
        client.sendMessage({
            type: 'custom_message',
            data: 'Hello from client!'
        });
        
        // Keep connection alive for 10 seconds
        setTimeout(() => {
            client.disconnect();
        }, 10000);
        
    } catch (error) {
        console.error('Error:', error);
    }
}

main();
```

## Python Client Example

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
        print(f"Connected to WebSocket for user {self.user_id}")
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
    
    async def send_message(self, message: Dict[str, Any]):
        """Send a message to the server"""
        if not self.websocket:
            raise Exception("WebSocket not connected")
        await self.websocket.send(json.dumps(message))
    
    async def ping(self):
        """Send ping message"""
        await self.send_message({"type": "ping"})
    
    async def request_motivation(self, current_challenge: str = "", stress_level: int = 5):
        """Request motivation message"""
        await self.send_message({
            "type": "motivation_requested",
            "current_challenge": current_challenge,
            "stress_level": stress_level
        })
    
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
            
            # Send initial messages
            await self.ping()
            await self.request_motivation("Working on integration", 7)
            
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
    def on_pong(message):
        print(f"Pong received: {message['message']}")
    
    def on_motivation(message):
        print(f"Motivation: {message['motivation_text']}")
        print(f"Challenge: {message['current_challenge']}")
        print(f"Stress Level: {message['stress_level']}")
    
    def on_echo(message):
        print(f"Echo: {message['message']}")
    
    client.on_message("pong", on_pong)
    client.on_message("motivation_generated", on_motivation)
    client.on_message("echo", on_echo)
    
    # Run client for 10 seconds
    await client.run(10)

# Run the example
if __name__ == "__main__":
    asyncio.run(main())
```

## WebSocket Status Endpoint

**GET** `/api/v1/ws/status`

Returns the current WebSocket connection status:

```json
{
  "connected_users": 5,
  "status": "active"
}
```

## Error Handling

### Connection Errors
- **Connection Refused**: Server not running or wrong URL
- **Authentication**: User ID validation (if implemented)
- **Network Issues**: Handle reconnection logic

### Message Errors
- **Invalid JSON**: Messages must be valid JSON
- **Missing Type**: Messages should include a `type` field
- **Server Errors**: Handle server-side exceptions

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

# Test WebSocket with wscat
wscat -c ws://localhost:8000/api/v1/ws/123456789

# Send test messages
{"type": "ping"}
{"type": "motivation_requested", "current_challenge": "Testing", "stress_level": 5}
```

## Best Practices

1. **Reconnection Logic**: Implement automatic reconnection on disconnect
2. **Heartbeat**: Use ping/pong to keep connections alive
3. **Error Handling**: Handle connection and message errors gracefully
4. **Message Validation**: Validate message format before sending
5. **Resource Cleanup**: Properly close connections when done

## Security Considerations

- **User Authentication**: Validate user_id on connection
- **Message Validation**: Sanitize incoming messages
- **Rate Limiting**: Implement rate limiting for message sending
- **Connection Limits**: Limit number of connections per user

## Testing

### Test Connection
```bash
# Using wscat (install with: npm install -g wscat)
wscat -c ws://localhost:8000/api/v1/ws/123456789

# Send a ping message
{"type": "ping"}

# Request motivation
{"type": "motivation_requested", "current_challenge": "Testing", "stress_level": 5}
```

### Test Status Endpoint
```bash
curl http://localhost:8000/api/v1/ws/status
```

## Integration with Task Management

The WebSocket can be extended to provide real-time updates for:

- Task completion notifications
- Goal progress updates
- AI-generated motivation messages
- Real-time collaboration features
- Progress tracking updates

## Example Use Cases

1. **Real-time Motivation**: Request motivation when feeling stuck
2. **Task Updates**: Receive notifications when tasks are completed
3. **Progress Tracking**: Real-time progress updates
4. **Collaboration**: Real-time updates for team members
5. **AI Integration**: Real-time AI-generated insights and recommendations
