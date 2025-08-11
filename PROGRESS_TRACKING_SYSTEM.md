# Progress Tracking System

## Overview
Backend supports the progress tracking UI with mood, energy, focus metrics, goal countdown, and AI insights.

## ✅ Supported Features
- **Mood/Energy/Focus**: 1-10 scale tracking
- **Goal Countdown**: Days until target date
- **Progress Analytics**: 30-day averages and trends
- **AI Insights**: Automated analysis and recommendations

## 🔌 Key APIs

### Create Progress Entry
```http
POST /progress-logs/
{
  "user_id": "123456789",
  "mood_score": 8,
  "energy_level": 7,
  "focus_score": 9,
  "tasks_completed": 5,
  "tasks_planned": 6
}
```

### Get Statistics
```http
GET /progress-logs/user/{user_id}/stats?days=30
```
Returns: `avg_mood_score`, `avg_energy_level`, `avg_focus_score`, `completion_rate`

### Get Goal Countdown
```http
GET /motivation/stats/{user_id}
```
Returns: `days_until_target`, `user_phase`, `completion_rate_30_days`

## 🎨 Frontend Integration

### Convert to Percentages
```javascript
const toPercentage = (score) => (score / 10) * 100;
// 7.2 → 72%, 6.5 → 65%, 7.8 → 78%
```

### Progress Data Structure
```javascript
{
  mood: 72,           // Percentage
  energy: 65,         // Percentage  
  focus: 78,          // Percentage
  daysUntilTarget: 223,
  overallProgress: 68 // Calculate from goals/tasks
}
```

## 📊 Data Models
```python
ProgressLog:
  mood_score: int (1-10)
  energy_level: int (1-10)
  focus_score: int (1-10)
  tasks_completed: int
  tasks_planned: int

User:
  quit_job_target: date  # For countdown
  current_phase: PhaseEnum
```

## 🚀 Quick Start
1. Create progress entry: `POST /progress-logs/`
2. Get stats: `GET /progress-logs/user/{id}/stats`
3. Get countdown: `GET /motivation/stats/{id}`
4. Convert scores to percentages for UI
5. Use WebSocket for real-time updates: `ws://localhost:8000/api/v1/ws`

## 🔧 Service Functions
```python
create_progress_log(session, data) -> ProgressLog
user_progress_stats(session, user_id, days=30) -> dict
list_user_recent_progress_logs(session, user_id, days=7) -> List[ProgressLog]
```

**Backend fully supports the UI. Just connect frontend to existing APIs.**
