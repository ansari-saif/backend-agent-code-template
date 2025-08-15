#!/usr/bin/env python3
"""
Example: Creating and Tracking Hierarchical Goals

This script demonstrates how to create parent-child goal relationships
and track progress across the hierarchy.
"""

from datetime import date
from sqlmodel import Session, create_engine, select
from app.core.database import get_session
from app.models.goal import Goal
from app.models.user import User
from app.schemas.goal import GoalTypeEnum, StatusEnum, PhaseEnum, PriorityEnum
from app.services import goal_service

# Example user ID (replace with actual user ID)
USER_ID = "123456789"

def create_hierarchical_goals_example():
    """Create a complete goal hierarchy example."""
    
    # Connect to database
    engine = create_engine("postgresql://user:password@localhost/diary_db")
    
    with Session(engine) as session:
        # 1. Create a Yearly Goal (Parent)
        yearly_goal = Goal(
            user_id=USER_ID,
            type=GoalTypeEnum.YEARLY,
            description="Build a successful side business",
            deadline=date(2025, 12, 31),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.HIGH,
            completion_percentage=0.0
        )
        session.add(yearly_goal)
        session.commit()
        session.refresh(yearly_goal)
        print(f"✅ Created Yearly Goal: {yearly_goal.description} (ID: {yearly_goal.goal_id})")
        
        # 2. Create Quarterly Goals (Children of Yearly)
        q1_goal = Goal(
            user_id=USER_ID,
            parent_goal_id=yearly_goal.goal_id,
            type=GoalTypeEnum.QUARTERLY,
            description="Validate business idea and create MVP",
            deadline=date(2025, 3, 31),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.HIGH,
            completion_percentage=0.0
        )
        
        q2_goal = Goal(
            user_id=USER_ID,
            parent_goal_id=yearly_goal.goal_id,
            type=GoalTypeEnum.QUARTERLY,
            description="Launch MVP and get first 10 customers",
            deadline=date(2025, 6, 30),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.MVP,
            priority=PriorityEnum.HIGH,
            completion_percentage=0.0
        )
        
        session.add_all([q1_goal, q2_goal])
        session.commit()
        session.refresh(q1_goal)
        session.refresh(q2_goal)
        print(f"✅ Created Q1 Goal: {q1_goal.description} (ID: {q1_goal.goal_id})")
        print(f"✅ Created Q2 Goal: {q2_goal.description} (ID: {q2_goal.goal_id})")
        
        # 3. Create Monthly Goals (Children of Q1)
        jan_goal = Goal(
            user_id=USER_ID,
            parent_goal_id=q1_goal.goal_id,
            type=GoalTypeEnum.MONTHLY,
            description="Research market and define product features",
            deadline=date(2025, 1, 31),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.HIGH,
            completion_percentage=0.0
        )
        
        feb_goal = Goal(
            user_id=USER_ID,
            parent_goal_id=q1_goal.goal_id,
            type=GoalTypeEnum.MONTHLY,
            description="Design and prototype core features",
            deadline=date(2025, 2, 28),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.HIGH,
            completion_percentage=0.0
        )
        
        mar_goal = Goal(
            user_id=USER_ID,
            parent_goal_id=q1_goal.goal_id,
            type=GoalTypeEnum.MONTHLY,
            description="Build MVP and test with 5 users",
            deadline=date(2025, 3, 31),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.MVP,
            priority=PriorityEnum.HIGH,
            completion_percentage=0.0
        )
        
        session.add_all([jan_goal, feb_goal, mar_goal])
        session.commit()
        session.refresh(jan_goal)
        session.refresh(feb_goal)
        session.refresh(mar_goal)
        print(f"✅ Created Jan Goal: {jan_goal.description} (ID: {jan_goal.goal_id})")
        print(f"✅ Created Feb Goal: {feb_goal.description} (ID: {feb_goal.goal_id})")
        print(f"✅ Created Mar Goal: {mar_goal.description} (ID: {mar_goal.goal_id})")
        
        # 4. Create Weekly Goals (Children of Jan)
        week1_goal = Goal(
            user_id=USER_ID,
            parent_goal_id=jan_goal.goal_id,
            type=GoalTypeEnum.WEEKLY,
            description="Interview 10 potential customers",
            deadline=date(2025, 1, 7),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.HIGH,
            completion_percentage=0.0
        )
        
        week2_goal = Goal(
            user_id=USER_ID,
            parent_goal_id=jan_goal.goal_id,
            type=GoalTypeEnum.WEEKLY,
            description="Analyze competitor products",
            deadline=date(2025, 1, 14),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.MEDIUM,
            completion_percentage=0.0
        )
        
        session.add_all([week1_goal, week2_goal])
        session.commit()
        session.refresh(week1_goal)
        session.refresh(week2_goal)
        print(f"✅ Created Week 1 Goal: {week1_goal.description} (ID: {week1_goal.goal_id})")
        print(f"✅ Created Week 2 Goal: {week2_goal.description} (ID: {week2_goal.goal_id})")
        
        # 5. Demonstrate Progress Tracking
        print("\n📊 Progress Tracking Demo:")
        
        # Update weekly goal progress
        week1_goal.completion_percentage = 75.0
        session.add(week1_goal)
        session.commit()
        print(f"✅ Updated Week 1 progress to 75%")
        
        # Update another weekly goal
        week2_goal.completion_percentage = 50.0
        session.add(week2_goal)
        session.commit()
        print(f"✅ Updated Week 2 progress to 50%")
        
        # Update monthly goal progress
        jan_goal.completion_percentage = 60.0
        session.add(jan_goal)
        session.commit()
        print(f"✅ Updated Jan progress to 60%")
        
        # 6. Show Hierarchy and Progress Calculation
        print("\n🏗️ Goal Hierarchy:")
        
        # Get yearly goal with hierarchy
        yearly_hierarchy = goal_service.get_goal_hierarchy(session, yearly_goal.goal_id)
        print(f"Yearly Goal: {yearly_hierarchy.description}")
        print(f"  - Progress: {yearly_hierarchy.completion_percentage}%")
        print(f"  - Child goals: {len(yearly_hierarchy.child_goals)}")
        
        for q_goal in yearly_hierarchy.child_goals:
            print(f"  └─ Q{['1', '2', '3', '4'][q_goal.deadline.month//3-1]} Goal: {q_goal.description}")
            print(f"     - Progress: {q_goal.completion_percentage}%")
            
            # Get children of quarterly goal
            q_children = goal_service.get_child_goals(session, q_goal.goal_id)
            for m_goal in q_children:
                print(f"     └─ {m_goal.deadline.strftime('%b')} Goal: {m_goal.description}")
                print(f"        - Progress: {m_goal.completion_percentage}%")
                
                # Get children of monthly goal
                m_children = goal_service.get_child_goals(session, m_goal.goal_id)
                for w_goal in m_children:
                    print(f"        └─ Week Goal: {w_goal.description}")
                    print(f"           - Progress: {w_goal.completion_percentage}%")
        
        # 7. Demonstrate Automatic Progress Updates
        print("\n🔄 Automatic Progress Updates:")
        
        # Update a child goal and see parent progress update
        week1_goal.completion_percentage = 100.0  # Complete week 1
        session.add(week1_goal)
        session.commit()
        
        # Manually update parent progress
        goal_service.update_goal_hierarchy_progress(session, jan_goal.goal_id)
        session.refresh(jan_goal)
        print(f"✅ After completing Week 1, Jan progress updated to: {jan_goal.completion_percentage}%")
        
        # Update quarterly progress
        goal_service.update_goal_hierarchy_progress(session, q1_goal.goal_id)
        session.refresh(q1_goal)
        print(f"✅ Q1 progress updated to: {q1_goal.completion_percentage}%")
        
        # Update yearly progress
        goal_service.update_goal_hierarchy_progress(session, yearly_goal.goal_id)
        session.refresh(yearly_goal)
        print(f"✅ Yearly progress updated to: {yearly_goal.completion_percentage}%")
        
        print("\n🎯 Goal Hierarchy Tracking Complete!")
        print("You can now:")
        print("- Create parent-child goal relationships")
        print("- Track progress automatically up the hierarchy")
        print("- View goal hierarchies with /goals/{id}/hierarchy endpoint")
        print("- Get child goals with /goals/{id}/children endpoint")
        print("- Get parent goals with /goals/{id}/parent endpoint")

if __name__ == "__main__":
    create_hierarchical_goals_example()
