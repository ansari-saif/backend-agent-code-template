import pytest
from datetime import date
from sqlmodel import Session, select
from app.models.goal import Goal
from app.schemas.goal import GoalTypeEnum, StatusEnum, PhaseEnum, PriorityEnum
from app.services import goal_service


@pytest.mark.integration
class TestHierarchicalGoals:
    """Test hierarchical goal relationships and progress tracking."""
    
    def test_create_parent_child_goals(self, session: Session, test_user):
        """Test creating goals with parent-child relationships."""
        # Create parent goal
        parent_goal = Goal(
            user_id=test_user.telegram_id,
            type=GoalTypeEnum.QUARTERLY,
            description="Parent Goal",
            deadline=date(2025, 3, 31),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.HIGH,
            completion_percentage=0.0
        )
        session.add(parent_goal)
        session.commit()
        session.refresh(parent_goal)
        
        # Create child goal
        child_goal = Goal(
            user_id=test_user.telegram_id,
            parent_goal_id=parent_goal.goal_id,
            type=GoalTypeEnum.MONTHLY,
            description="Child Goal",
            deadline=date(2025, 1, 31),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.MEDIUM,
            completion_percentage=0.0
        )
        session.add(child_goal)
        session.commit()
        session.refresh(child_goal)
        
        # Verify relationships
        assert child_goal.parent_goal_id == parent_goal.goal_id
        # SQLModel automatically loads the relationship, so parent_goal should be loaded
        assert child_goal.parent_goal is not None
        assert child_goal.parent_goal.goal_id == parent_goal.goal_id
        
        # Test service functions
        loaded_child = goal_service.get_parent_goal(session, child_goal.goal_id)
        assert loaded_child is not None
        assert loaded_child.goal_id == parent_goal.goal_id
        
        children = goal_service.get_child_goals(session, parent_goal.goal_id)
        assert len(children) == 1
        assert children[0].goal_id == child_goal.goal_id
    
    def test_goal_hierarchy_loading(self, session: Session, test_user):
        """Test loading goal hierarchy with parent and children."""
        # Create hierarchy: Parent -> Child1, Child2
        parent_goal = Goal(
            user_id=test_user.telegram_id,
            type=GoalTypeEnum.QUARTERLY,
            description="Parent Goal",
            deadline=date(2025, 3, 31),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.HIGH,
            completion_percentage=0.0
        )
        session.add(parent_goal)
        session.commit()
        session.refresh(parent_goal)
        
        child1 = Goal(
            user_id=test_user.telegram_id,
            parent_goal_id=parent_goal.goal_id,
            type=GoalTypeEnum.MONTHLY,
            description="Child 1",
            deadline=date(2025, 1, 31),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.MEDIUM,
            completion_percentage=50.0
        )
        
        child2 = Goal(
            user_id=test_user.telegram_id,
            parent_goal_id=parent_goal.goal_id,
            type=GoalTypeEnum.MONTHLY,
            description="Child 2",
            deadline=date(2025, 2, 28),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.MEDIUM,
            completion_percentage=75.0
        )
        
        session.add_all([child1, child2])
        session.commit()
        
        # Test hierarchy loading
        hierarchy = goal_service.get_goal_hierarchy(session, parent_goal.goal_id)
        assert hierarchy is not None
        assert hierarchy.goal_id == parent_goal.goal_id
        assert len(hierarchy.child_goals) == 2
        assert hierarchy.parent_goal is None  # No parent
        
        # Test child hierarchy loading
        child_hierarchy = goal_service.get_goal_hierarchy(session, child1.goal_id)
        assert child_hierarchy is not None
        assert child_hierarchy.goal_id == child1.goal_id
        assert len(child_hierarchy.child_goals) == 0  # No children
        assert child_hierarchy.parent_goal is not None
        assert child_hierarchy.parent_goal.goal_id == parent_goal.goal_id
    
    def test_progress_calculation(self, session: Session, test_user):
        """Test automatic progress calculation based on children."""
        # Create parent goal
        parent_goal = Goal(
            user_id=test_user.telegram_id,
            type=GoalTypeEnum.QUARTERLY,
            description="Parent Goal",
            deadline=date(2025, 3, 31),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.HIGH,
            completion_percentage=0.0
        )
        session.add(parent_goal)
        session.commit()
        session.refresh(parent_goal)
        
        # Create children with different progress
        child1 = Goal(
            user_id=test_user.telegram_id,
            parent_goal_id=parent_goal.goal_id,
            type=GoalTypeEnum.MONTHLY,
            description="Child 1",
            deadline=date(2025, 1, 31),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.MEDIUM,
            completion_percentage=50.0
        )
        
        child2 = Goal(
            user_id=test_user.telegram_id,
            parent_goal_id=parent_goal.goal_id,
            type=GoalTypeEnum.MONTHLY,
            description="Child 2",
            deadline=date(2025, 2, 28),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.MEDIUM,
            completion_percentage=75.0
        )
        
        session.add_all([child1, child2])
        session.commit()
        
        # Test progress calculation
        calculated_progress = goal_service.calculate_goal_progress(session, parent_goal.goal_id)
        expected_progress = (50.0 + 75.0) / 2  # Average of children
        assert calculated_progress == expected_progress
        
        # Test automatic progress update
        goal_service.update_goal_hierarchy_progress(session, parent_goal.goal_id)
        session.refresh(parent_goal)
        assert parent_goal.completion_percentage == expected_progress
    
    def test_goals_by_type(self, session: Session, test_user):
        """Test filtering goals by type."""
        # Create goals of different types
        yearly_goal = Goal(
            user_id=test_user.telegram_id,
            type=GoalTypeEnum.YEARLY,
            description="Yearly Goal",
            deadline=date(2025, 12, 31),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.HIGH,
            completion_percentage=0.0
        )
        
        monthly_goal = Goal(
            user_id=test_user.telegram_id,
            type=GoalTypeEnum.MONTHLY,
            description="Monthly Goal",
            deadline=date(2025, 1, 31),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.MEDIUM,
            completion_percentage=0.0
        )
        
        weekly_goal = Goal(
            user_id=test_user.telegram_id,
            type=GoalTypeEnum.WEEKLY,
            description="Weekly Goal",
            deadline=date(2025, 1, 7),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.LOW,
            completion_percentage=0.0
        )
        
        session.add_all([yearly_goal, monthly_goal, weekly_goal])
        session.commit()
        
        # Test filtering by type
        yearly_goals = goal_service.list_goals_by_type(session, test_user.telegram_id, GoalTypeEnum.YEARLY)
        assert len(yearly_goals) == 1
        assert yearly_goals[0].type == GoalTypeEnum.YEARLY
        
        monthly_goals = goal_service.list_goals_by_type(session, test_user.telegram_id, GoalTypeEnum.MONTHLY)
        assert len(monthly_goals) == 1
        assert monthly_goals[0].type == GoalTypeEnum.MONTHLY
        
        weekly_goals = goal_service.list_goals_by_type(session, test_user.telegram_id, GoalTypeEnum.WEEKLY)
        assert len(weekly_goals) == 1
        assert weekly_goals[0].type == GoalTypeEnum.WEEKLY
    
    def test_goal_without_children_progress(self, session: Session, test_user):
        """Test progress calculation for goals without children."""
        goal = Goal(
            user_id=test_user.telegram_id,
            type=GoalTypeEnum.MONTHLY,
            description="Standalone Goal",
            deadline=date(2025, 1, 31),
            status=StatusEnum.ACTIVE,
            phase=PhaseEnum.RESEARCH,
            priority=PriorityEnum.MEDIUM,
            completion_percentage=25.0
        )
        session.add(goal)
        session.commit()
        session.refresh(goal)
        
        # Progress should remain unchanged for goals without children
        calculated_progress = goal_service.calculate_goal_progress(session, goal.goal_id)
        assert calculated_progress == 25.0
