import pytest
from datetime import datetime
from app.schemas.ai_context import AIContextBase, AIContextCreate, AIContextResponse, AIContextUpdate


@pytest.mark.unit
def test_ai_context_base():
    now = datetime.utcnow()
    data = {
        "user_id": "test_user_123",
        "behavior_patterns": "{'morning_person': true}",
        "productivity_insights": "{'peak_hours': ['9-11', '15-17']}",
        "motivation_triggers": "{'rewards': ['completion', 'progress']}",
        "stress_indicators": "{'high_workload': true}",
        "optimal_work_times": "['morning', 'late_afternoon']"
    }
    
    context = AIContextBase(**data)
    assert context.user_id == data["user_id"]
    assert context.behavior_patterns == data["behavior_patterns"]
    assert context.productivity_insights == data["productivity_insights"]
    assert context.motivation_triggers == data["motivation_triggers"]
    assert context.stress_indicators == data["stress_indicators"]
    assert context.optimal_work_times == data["optimal_work_times"]


@pytest.mark.unit
def test_ai_context_create():
    data = {
        "user_id": "test_user_123",
        "behavior_patterns": "{'morning_person': true}"
    }
    
    context = AIContextCreate(**data)
    assert context.user_id == data["user_id"]
    assert context.behavior_patterns == data["behavior_patterns"]
    assert context.productivity_insights is None
    assert context.motivation_triggers is None
    assert context.stress_indicators is None
    assert context.optimal_work_times is None


@pytest.mark.unit
def test_ai_context_response():
    now = datetime.utcnow()
    data = {
        "context_id": 1,
        "user_id": "test_user_123",
        "behavior_patterns": "{'morning_person': true}",
        "last_updated": now
    }
    
    context = AIContextResponse(**data)
    assert context.context_id == data["context_id"]
    assert context.user_id == data["user_id"]
    assert context.behavior_patterns == data["behavior_patterns"]
    assert context.last_updated == now


@pytest.mark.unit
def test_ai_context_update():
    data = {
        "behavior_patterns": "{'morning_person': false}",
        "productivity_insights": "{'peak_hours': ['10-12', '14-16']}"
    }
    
    context = AIContextUpdate(**data)
    assert context.behavior_patterns == data["behavior_patterns"]
    assert context.productivity_insights == data["productivity_insights"]
    assert context.motivation_triggers is None
    assert context.stress_indicators is None
    assert context.optimal_work_times is None
