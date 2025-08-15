# Hierarchical Goal Tracking Guide

## Overview

The Diary application now supports **hierarchical goal relationships**, allowing you to create parent-child goal structures. This enables better tracking of how smaller goals contribute to larger objectives.

## Goal Hierarchy Structure

```
Yearly Goal
├── Q1 Goal
│   ├── January Goal
│   │   ├── Week 1 Goal
│   │   └── Week 2 Goal
│   ├── February Goal
│   └── March Goal
├── Q2 Goal
├── Q3 Goal
└── Q4 Goal
```

## Key Features

### 1. Parent-Child Relationships
- **`parent_goal_id`**: Links a goal to its parent goal
- **Automatic relationship loading**: SQLModel automatically loads parent and child goals
- **Hierarchical progress tracking**: Parent goals automatically calculate progress based on children

### 2. Progress Calculation
- **Child-based calculation**: Parent goal progress = average of all child goal progress
- **Automatic updates**: When child goals are updated, parent progress is recalculated
- **Recursive updates**: Changes cascade up the entire hierarchy

### 3. API Endpoints

#### Create Goals with Parent
```bash
POST /api/v1/goals/
{
  "user_id": "123456789",
  "parent_goal_id": 1,  # Link to parent goal
  "type": "Monthly",
  "description": "Child goal description",
  "deadline": "2025-01-31",
  "phase": "Research",
  "priority": "High"
}
```

#### View Goal Hierarchy
```bash
GET /api/v1/goals/{goal_id}/hierarchy
```
Returns goal with loaded parent and child goals.

#### Get Child Goals
```bash
GET /api/v1/goals/{goal_id}/children
```
Returns all child goals of a parent goal.

#### Get Parent Goal
```bash
GET /api/v1/goals/{goal_id}/parent
```
Returns the parent goal of a child goal.

#### Filter Goals by Type
```bash
GET /api/v1/goals/user/{user_id}/type/{goal_type}
```
Get all goals of a specific type (Yearly, Quarterly, Monthly, Weekly).

#### Update Goal Progress
```bash
POST /api/v1/goals/{goal_id}/update-progress
```
Manually trigger progress recalculation for a goal and its parents.

## Usage Examples

### 1. Creating a Goal Hierarchy

```python
from datetime import date
from app.models.goal import Goal
from app.schemas.goal import GoalTypeEnum, StatusEnum, PhaseEnum, PriorityEnum

# 1. Create Yearly Goal (Parent)
yearly_goal = Goal(
    user_id="123456789",
    type=GoalTypeEnum.YEARLY,
    description="Build a successful side business",
    deadline=date(2025, 12, 31),
    status=StatusEnum.ACTIVE,
    phase=PhaseEnum.RESEARCH,
    priority=PriorityEnum.HIGH,
    completion_percentage=0.0
)

# 2. Create Quarterly Goal (Child of Yearly)
q1_goal = Goal(
    user_id="123456789",
    parent_goal_id=yearly_goal.goal_id,  # Link to parent
    type=GoalTypeEnum.QUARTERLY,
    description="Validate business idea and create MVP",
    deadline=date(2025, 3, 31),
    status=StatusEnum.ACTIVE,
    phase=PhaseEnum.RESEARCH,
    priority=PriorityEnum.HIGH,
    completion_percentage=0.0
)

# 3. Create Monthly Goal (Child of Quarterly)
jan_goal = Goal(
    user_id="123456789",
    parent_goal_id=q1_goal.goal_id,  # Link to parent
    type=GoalTypeEnum.MONTHLY,
    description="Research market and define product features",
    deadline=date(2025, 1, 31),
    status=StatusEnum.ACTIVE,
    phase=PhaseEnum.RESEARCH,
    priority=PriorityEnum.HIGH,
    completion_percentage=0.0
)
```

### 2. Tracking Progress

```python
from app.services import goal_service

# Update child goal progress
jan_goal.completion_percentage = 75.0
session.add(jan_goal)
session.commit()

# Automatically update parent progress
goal_service.update_goal_hierarchy_progress(session, q1_goal.goal_id)
goal_service.update_goal_hierarchy_progress(session, yearly_goal.goal_id)

# Check updated progress
session.refresh(q1_goal)
session.refresh(yearly_goal)
print(f"Q1 Progress: {q1_goal.completion_percentage}%")
print(f"Yearly Progress: {yearly_goal.completion_percentage}%")
```

### 3. Viewing Goal Hierarchies

```python
# Get complete hierarchy
hierarchy = goal_service.get_goal_hierarchy(session, yearly_goal.goal_id)
print(f"Yearly Goal: {hierarchy.description}")
print(f"Progress: {hierarchy.completion_percentage}%")
print(f"Child goals: {len(hierarchy.child_goals)}")

for child in hierarchy.child_goals:
    print(f"  └─ {child.type}: {child.description} ({child.completion_percentage}%)")
```

## Service Functions

### Core Functions

```python
# Get goal with parent and children loaded
goal_service.get_goal_hierarchy(session, goal_id)

# Get all child goals
goal_service.get_child_goals(session, parent_goal_id)

# Get parent goal
goal_service.get_parent_goal(session, child_goal_id)

# Filter goals by type
goal_service.list_goals_by_type(session, user_id, GoalTypeEnum.MONTHLY)

# Calculate progress based on children
goal_service.calculate_goal_progress(session, goal_id)

# Update progress recursively up hierarchy
goal_service.update_goal_hierarchy_progress(session, goal_id)
```

## Best Practices

### 1. Goal Structure
- **Yearly Goals**: High-level objectives for the year
- **Quarterly Goals**: Major milestones broken down from yearly goals
- **Monthly Goals**: Specific deliverables for each month
- **Weekly Goals**: Actionable tasks for each week

### 2. Progress Tracking
- Update child goals first, then let parent progress update automatically
- Use the `/update-progress` endpoint to manually trigger recalculation
- Monitor parent goal progress to ensure alignment with child goals

### 3. Goal Management
- Keep child goals specific and measurable
- Ensure child goals contribute directly to parent goal success
- Regularly review and adjust goal hierarchies as priorities change

## Database Schema

```sql
-- Goals table with parent-child relationship
CREATE TABLE goals (
    goal_id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    parent_goal_id INTEGER REFERENCES goals(goal_id),  -- Self-referencing foreign key
    type VARCHAR NOT NULL,
    description TEXT NOT NULL,
    deadline DATE,
    status VARCHAR NOT NULL,
    phase VARCHAR NOT NULL,
    priority VARCHAR NOT NULL,
    completion_percentage FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Migration Notes

The `parent_goal_id` field was added to the goals table via migration. Existing goals will have `parent_goal_id = NULL` and can be linked to parents by updating the field.

## Testing

Run the hierarchical goals tests:
```bash
python -m pytest tests/test_hierarchical_goals.py -v
```

## Example Script

See `example_hierarchical_goals.py` for a complete demonstration of creating and tracking hierarchical goals.

## Benefits

1. **Better Organization**: Clear structure showing how goals relate to each other
2. **Automatic Progress Tracking**: Parent goals automatically reflect child progress
3. **Strategic Alignment**: Ensure smaller goals contribute to larger objectives
4. **Visual Hierarchy**: Easy to see the big picture and drill down into details
5. **Flexible Structure**: Support for any depth of goal nesting

This hierarchical system makes it much easier to track how your daily and weekly efforts contribute to your larger monthly, quarterly, and yearly objectives!
