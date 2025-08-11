# Motivation System

The Motivation System is an AI-powered feature that generates personalized motivational messages for users based on their current situation, progress, and context.

## Features

### 🎯 AI-Powered Motivation Generation
- **Contextual Messages**: Generates motivation based on user's current challenge and stress level
- **Personalized Content**: Uses user's AI context, recent achievements, and entrepreneurial phase
- **Real-time Data**: Incorporates recent task completions and current progress
- **Stress-Aware**: Adapts messaging based on user's stress level (1-10 scale)

### 📊 Motivation Statistics
- **Completion Rates**: 30-day task completion statistics
- **Streak Tracking**: Current streak of days with completed tasks
- **Progress Metrics**: Recent achievements and pending tasks
- **Phase Information**: User's current entrepreneurial phase
- **Target Countdown**: Days until job transition target

### 🔌 Multiple Interfaces
- **REST API**: HTTP endpoints for motivation generation and stats
- **WebSocket**: Real-time motivation requests and responses
- **Service Layer**: Direct service integration for other components

## API Endpoints

### Generate Motivation
```http
POST /motivation/generate
```

**Request Body:**
```json
{
  "user_id": "123456789",
  "current_challenge": "Feeling overwhelmed with MVP development",
  "stress_level": 7
}
```

**Response:**
```json
{
  "user_id": "123456789",
  "motivation_text": "John, it's completely normal to feel overwhelmed when you're deep in the trenches of MVP development...",
  "current_challenge": "Feeling overwhelmed with MVP development",
  "stress_level": 7,
  "recent_achievements": 3,
  "pending_tasks": 5,
  "completion_rate": 75.5,
  "user_phase": "MVP",
  "days_until_target": 120
}
```

### Get Motivation Stats
```http
GET /motivation/stats/{user_id}
```

**Response:**
```json
{
  "user_id": "123456789",
  "total_tasks_30_days": 25,
  "completed_tasks_30_days": 18,
  "pending_tasks": 7,
  "completion_rate_30_days": 72.0,
  "current_streak_days": 5,
  "user_phase": "MVP",
  "days_until_target": 120
}
```

## WebSocket Interface

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/123456789');
```

### Request Motivation
```javascript
ws.send(JSON.stringify({
  "type": "motivation_requested",
  "current_challenge": "Feeling overwhelmed with MVP development",
  "stress_level": 7
}));
```

### Receive Motivation
```javascript
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  if (data.type === 'motivation_generated') {
    console.log('Motivation:', data.motivation_text);
    console.log('Stats:', data);
  }
};
```

## How It Works

### 1. Context Gathering
The system collects user context from multiple sources:
- **User Profile**: Current phase, energy profile, goals
- **AI Context**: Motivation triggers, behavior patterns, productivity insights
- **Recent Activity**: Completed tasks from the last 7 days
- **Current State**: Pending tasks, completion rates, streaks

### 2. AI Processing
The AI service generates personalized motivation using:
- **User's Current Challenge**: What they're struggling with
- **Stress Level**: How overwhelmed they feel (1-10)
- **Recent Achievements**: Recent task completions
- **Motivation Triggers**: What motivates this specific user
- **Entrepreneurial Phase**: MVP, Growth, Scaling, etc.

### 3. Response Generation
The system returns:
- **Personalized Message**: AI-generated motivation text
- **Context Data**: Current challenge, stress level
- **Progress Metrics**: Recent achievements, pending tasks, completion rate
- **Phase Information**: User's entrepreneurial phase
- **Target Information**: Days until job transition target

## Testing

### Run Tests
```bash
# Run all motivation tests
python -m pytest tests/test_motivation_integration.py -v

# Run specific test
python -m pytest tests/test_motivation_integration.py::TestMotivationService::test_generate_motivation_success -v
```

### Demo Script
```bash
# Run the demo script
python test_motivation_demo.py
```

### WebSocket Testing
1. Start the server: `python -m uvicorn app.main:app --reload`
2. Open `motivation_websocket_test.html` in a browser
3. Connect to WebSocket and request motivation

## Integration

### Service Usage
```python
from app.services.motivation_service import generate_motivation, get_motivation_stats

# Generate motivation
motivation_data = await generate_motivation(
    session=session,
    user_id="123456789",
    current_challenge="Feeling overwhelmed",
    stress_level=7
)

# Get stats
stats = get_motivation_stats(session=session, user_id="123456789")
```

### Error Handling
The system includes robust error handling:
- **User Not Found**: Returns 404 with appropriate error message
- **AI Service Failure**: Falls back to default motivation message
- **Missing AI Context**: Automatically creates default context
- **Database Errors**: Graceful degradation with fallback responses

## Configuration

### Environment Variables
- `GEMINI_API_KEY`: Required for AI motivation generation
- Database configuration (see main app config)

### AI Context
The system automatically creates AI context for users if none exists, with default motivation triggers like:
- Achievement
- Progress
- Recognition

## Future Enhancements

### Planned Features
- **Motivation History**: Track and analyze motivation patterns
- **Scheduled Motivation**: Automatic motivation at optimal times
- **Motivation Preferences**: User-customizable motivation styles
- **Integration Hooks**: Connect with external productivity tools
- **Analytics Dashboard**: Motivation effectiveness metrics

### Advanced AI Features
- **Emotion Detection**: Analyze user mood from text input
- **Predictive Motivation**: Anticipate when motivation is needed
- **Contextual Learning**: Improve motivation based on user responses
- **Multi-modal Input**: Support for voice, image, and text input

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   REST API       │    │   Service       │
│   Interface     │    │   Endpoints      │    │   Layer         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌──────────────────┐
                    │  Motivation      │
                    │  Service         │
                    └──────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Service    │    │   Task Service   │    │   AI Context    │
│   (Gemini)      │    │   (Recent Tasks) │    │   Service       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

The motivation system is designed to be:
- **Scalable**: Handles multiple users and concurrent requests
- **Reliable**: Includes fallback mechanisms and error handling
- **Extensible**: Easy to add new motivation types and features
- **Testable**: Comprehensive test coverage for all components
