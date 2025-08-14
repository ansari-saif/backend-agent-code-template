from datetime import datetime, timedelta, date
from typing import List, Dict, Any
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from app.core.database import engine
from app.models.task import Task, CompletionStatusEnum
from app.models.prompt import Prompt  # Only used if needed; not used in normal flow
from app.api.v1.routes.websocket import send_notification_service
import json
import os
import google.generativeai as genai


IST = ZoneInfo("Asia/Kolkata")


def _now_ist() -> datetime:
    return datetime.now(IST)


def _within_next_30_minute(task: Task, *, now_ist: datetime) -> bool:
    if not task.scheduled_for_date or not task.scheduled_for_time:
        return False
    if task.completion_status == CompletionStatusEnum.COMPLETED:
        return False
    if task.actual_duration:
        task.scheduled_for_time = task.scheduled_for_time + timedelta(minutes=task.actual_duration)
    task_dt = datetime.combine(task.scheduled_for_date, task.scheduled_for_time, IST)
    return now_ist <= task_dt < (now_ist + timedelta(minutes=30))


def _build_notification_message(task: Task) -> str:
    priority = getattr(task.priority, "value", str(task.priority))
    due_time = None
    try:
        if task.scheduled_for_time:
            due_time = task.scheduled_for_time.strftime("%H:%M")
    except Exception:
        due_time = None
    when = f" at {due_time}" if due_time else " soon"
    return (
        f"Your task '{task.description}' is due{when}. Stay on track. (Priority: {priority})"
    )


async def task_reminder_job() -> None:
    """Cron job: every minute, find tasks scheduled within next 30 minutes (IST),
    generate all reminder messages in a single AI call, persist prompts, and
    send notifications via in-process websocket service.
    """
    now_ist = _now_ist()
    today_ist = now_ist.date()
    with Session(engine) as session:
        tasks: List[Task] = session.exec(
            select(Task).where(Task.scheduled_for_date == today_ist)
        ).all()
        due_soon = [t for t in tasks if _within_next_30_minute(t, now_ist=now_ist)]

        if not due_soon:
            return

        # Build AI prompt with all tasks at once, with per-user context for today's tasks
        ai_items: List[Dict[str, Any]] = []
        for t in due_soon:
            ai_items.append({
                "task_id": t.task_id,
                "description": t.description,
                "current_time": now_ist.strftime("%H:%M"),
                "scheduled_for": f"{t.scheduled_for_date} {getattr(t, 'scheduled_for_time', None)}"
            })

        # Build per-user context of all of today's tasks (for tone and relevance)
        user_context: Dict[str, List[Dict[str, Any]]] = {}
        for t in tasks:
            entry = {
                "task_id": t.task_id,
                "description": t.description,
                "priority": getattr(t.priority, "value", str(t.priority)),
                "status": getattr(t.completion_status, "value", str(t.completion_status)),
                "scheduled_for_date": str(getattr(t, "scheduled_for_date", None)),
                "scheduled_for_time": getattr(t, "scheduled_for_time", None).strftime("%H:%M") if getattr(t, "scheduled_for_time", None) else None,
            }
            user_context.setdefault(t.user_id, []).append(entry)

        system_instructions = (
            "Act like a russian mafia"
        )

        formatting_rules = (
            "Output must be a JSON array (order preserved) where each element is: {task_id, message}. "
            "Mention this that your task is due in <int> minutes\"\n\n"
            "Dont include task id in the message"
        )

        context_block = (
            "Today's tasks context grouped by user_id (use only for relevance and tone, do not list it back):\n"
            + json.dumps(user_context, default=str)
            + "\n\nItems to generate reminders for (same order to be preserved):\n"
            + json.dumps(ai_items, default=str)
        )

        prompt_text = system_instructions + formatting_rules + context_block

        messages: List[Dict[str, Any]] = []
        try:
            # Direct AI call using Gemini generate_content
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not configured")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt_text)
            raw_text = (getattr(response, "text", "") or "").strip()
            # Extract JSON if fenced
            if "```json" in raw_text:
                start = raw_text.find("```json") + 7
                end = raw_text.find("```", start)
                raw_text = raw_text[start:end].strip()
            parsed = json.loads(raw_text)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and {"task_id", "message"}.issubset(item.keys()):
                        messages.append(item)
        except Exception:
            # Fallback only when AI call or parsing fails
            messages = []

        # Fallback: build default messages for all tasks not covered by AI
        covered_ids = {m.get("task_id") for m in messages}
        for t in due_soon:
            if t.task_id not in covered_ids:
                messages.append({
                    "task_id": t.task_id,
                    "user_id": t.user_id,
                    "message": _build_notification_message(t),
                })

        # Send notifications one by one (service also persists Prompt)
        for m in messages:
            user_id = tasks[0].user_id
            try:
                # Directly call websocket notification service (no HTTP)
                await send_notification_service({"user_id": str(user_id), "message": m.get("message", "")}, session)
            except Exception:
                # continue with others
                pass


