You're asking about how weekly progress tracking works based on weekly goals. Let me examine the current implementation and show you how it calculates progress from weekly goals.

Search files...
Search files...
Based on my analysis, here's how **weekly progress tracking works based on weekly goals** in your backend:

## 📊 **Weekly Progress Calculation Methods**

### 1. **Goal-Based Progress (Primary Method)**
```python
# Weekly goals have completion_percentage field
weekly_goal = Goal(
    type=GoalTypeEnum.WEEKLY,
    description="Interview 5 potential customers",
    completion_percentage=40.0  # 40% complete
)

# Progress calculation from goals
goal_progress = len([g for g in goals if g.status == StatusEnum.COMPLETED]) / max(len(goals), 1) * 100
```

### 2. **Task-Based Progress (Secondary Method)**
```python
# From progress logs (daily task completion)
completion_rate = (total_completed / max(total_planned, 1)) * 100

# From weekly analysis
total_planned = sum(log.tasks_planned for log in progress_logs)
total_completed = sum(log.tasks_completed for log in progress_logs)
weekly_completion_rate = (total_completed / max(total_planned, 1)) * 100
```

## 🔧 **Current Implementation**

### Weekly Goal Structure
```python
Goal:
  type: GoalTypeEnum.WEEKLY
  description: str
  completion_percentage: float (0.0-100.0)
  status: StatusEnum (ACTIVE/COMPLETED/PAUSED)
  deadline: date
```

### Progress Calculation Logic
```python
# In AI service - weekly analysis
goal_progress = len([g for g in goals if g.status == StatusEnum.COMPLETED]) / max(len(goals), 1) * 100

# For active goals, use completion_percentage
active_goals_completion = [g.completion_percentage for g in goals if g.status == StatusEnum.ACTIVE]
avg_completion_percentage = sum(active_goals_completion) / max(len(active_goals_completion), 1)
```

## 🎯 **For Weekly Roadmap UI**

### Get Weekly Goals
```http
GET /goals/?user_id={user_id}&type=WEEKLY
```

### Calculate Weekly Progress
```javascript
const calculateWeeklyProgress = (weeklyGoals) => {
  const completed = weeklyGoals.filter(g => g.status === 'COMPLETED').length;
  const total = weeklyGoals.length;
  const activeProgress = weeklyGoals
    .filter(g => g.status === 'ACTIVE')
    .reduce((sum, g) => sum + g.completion_percentage, 0);
  
  return {
    completed,
    total,
    percentage: total > 0 ? ((completed / total) * 100) + (activeProgress / total) : 0
  };
};
```

## 📈 **API Endpoints for Weekly Progress**

### Get Weekly Analysis
```http
POST /ai/weekly-analysis
{
  "user_id": "123456789",
  "weeks": 1
}
```

### Get Goals Analysis
```http
POST /ai/analyze-goals
{
  "user_id": "123456789"
}
```

## 🔄 **Progress Update Flow**

1. **Create Weekly Goal**: `POST /goals/` with `type: "WEEKLY"`
2. **Update Progress**: `PUT /goals/{id}` with new `completion_percentage`
3. **Complete Goal**: Set `status: "COMPLETED"`
4. **Calculate Overall**: Sum of all weekly goal progress

**The system tracks weekly progress through both goal completion percentages and daily task completion rates, giving you comprehensive weekly milestone tracking!** 🎯