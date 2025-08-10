import google.generativeai as genai
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from app.models.user import User
from app.models.goal import Goal
from app.models.task import Task
from app.schemas.goal import StatusEnum
from app.schemas.task import CompletionStatusEnum, TaskPriorityEnum, EnergyRequiredEnum
from app.models.progress_log import ProgressLog
from app.models.ai_context import AIContext
from app.models.job_metrics import JobMetrics
from app.models.day_log import DayLog
from app.models.log import Log
from sqlmodel import Session, select
from typing import Optional


class AIService:
    def __init__(self):
        """Initialize the AI service with Gemini API if available; otherwise run in fallback mode."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    async def generate_daily_tasks(
        self,
        user: User,
        recent_progress: List[ProgressLog],
        pending_goals: List[Goal],
        today_energy_level: int = 5
    ) -> List[Dict[str, Any]]:
        """
        AI Agent 1: Daily Task Generator
        Generate personalized daily tasks based on user's goals, energy level, and recent progress.
        """
        try:
            # Calculate recent performance metrics
            if recent_progress:
                avg_completion = sum(log.tasks_completed for log in recent_progress) / len(recent_progress)
                avg_energy = sum(log.energy_level for log in recent_progress) / len(recent_progress)
                completion_trend = "improving" if recent_progress[-1].tasks_completed > avg_completion else "declining"
            else:
                avg_completion = 0
                avg_energy = 5
                completion_trend = "neutral"
            
            # Prepare goals context
            goals_context = []
            for goal in pending_goals:
                goals_context.append({
                    "description": goal.description,
                    "priority": goal.priority.value,
                    "completion": goal.completion_percentage,
                    "phase": goal.phase.value
                })
            
            prompt = f"""
            Generate daily tasks for an entrepreneur based on:
            
            User Profile:
            - Name: {user.name}
            - Phase: {user.current_phase}
            - Energy Profile: {user.energy_profile}
            - Energy Level: {today_energy_level}/10
            
            Recent Performance:
            - Average Task Completion: {avg_completion:.1f}
            - Completion Trend: {completion_trend}
            - Average Energy: {avg_energy:.1f}/10
            
            Goals:
            {json.dumps(goals_context, indent=2)}
            
            Generate tasks in JSON format:
            [
                {{
                    "description": "Task description",
                    "estimated_duration": 60,
                    "energy_required": "High/Medium/Low",
                    "priority": "Urgent/High/Medium/Low"
                }}
            ]
            
            Guidelines:
            - Generate 3-5 tasks based on energy level
            - Prioritize tasks aligned with goals
            - Match task difficulty with energy level
            - Include mix of quick wins and important tasks
            - Keep total duration realistic (4-6 hours max)
            """
            
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text
            
            tasks_data = json.loads(json_text)
            return tasks_data
            
        except Exception as e:
            # Fallback: Generate basic tasks
            return [
                {
                    "description": "Review and prioritize today's goals",
                    "priority": TaskPriorityEnum.HIGH.value,
                    "energy_required": EnergyRequiredEnum.LOW.value,
                    "estimated_duration": 30
                },
                {
                    "description": "Work on highest priority project task",
                    "priority": TaskPriorityEnum.HIGH.value,
                    "energy_required": EnergyRequiredEnum.MEDIUM.value,
                    "estimated_duration": 120
                }
            ]

    async def generate_motivation_message(self, user: User, ai_context: AIContext, current_challenge: str, stress_level: int, recent_completions: List[Task]) -> str:
        """
        AI Agent 2: Contextual Motivation
        Generate personalized motivation messages based on user's current situation and past behavior.
        """
        try:
            context_parts = [
                f"User: {user.name}, Current Phase: {user.current_phase}",
                f"Current Challenge: {current_challenge}",
                f"Stress Level: {stress_level}/10",
                f"Motivation Triggers: {ai_context.motivation_triggers or 'Achievement, Progress, Recognition'}",
            ]
            
            if recent_completions:
                recent_achievements = [task.description for task in recent_completions[-3:]]
                context_parts.append(f"Recent Achievements: {'; '.join(recent_achievements)}")
            
            if user.quit_job_target:
                days_until_target = (user.quit_job_target - date.today()).days
                context_parts.append(f"Days until job transition target: {days_until_target}")
            
            prompt = f"""
            Generate a personalized, encouraging message for an entrepreneur based on:
            
            {chr(10).join(context_parts)}
            
            The message should:
            - Be empathetic and understanding of their current challenge
            - Reference their recent achievements if any
            - Align with their known motivation triggers
            - Be specific to their entrepreneurial phase
            - Include actionable encouragement
            - Keep it concise (2-3 sentences)
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"You're making progress on your entrepreneurial journey, {user.name}! Every challenge you face is building the resilience you'll need to successfully transition from your job. Keep focusing on your goals - you're closer than you think!"



    async def generate_weekly_analysis(self, progress_logs: List[ProgressLog], goals: List[Goal], tasks: List[Task]) -> Dict[str, Any]:
        """
        AI Agent 4: Weekly Intelligence Analyzer
        Analyze weekly patterns and provide insights for productivity optimization.
        """
        try:
            # Calculate metrics
            if progress_logs:
                avg_completion = sum(log.tasks_completed for log in progress_logs) / len(progress_logs)
                avg_mood = sum(log.mood_score for log in progress_logs) / len(progress_logs)
                avg_energy = sum(log.energy_level for log in progress_logs) / len(progress_logs)
                avg_focus = sum(log.focus_score for log in progress_logs) / len(progress_logs)
                total_planned = sum(log.tasks_planned for log in progress_logs)
                total_completed = sum(log.tasks_completed for log in progress_logs)
                completion_rate = (total_completed / max(total_planned, 1)) * 100
            else:
                avg_completion = avg_mood = avg_energy = avg_focus = completion_rate = 0
            
            goal_progress = len([g for g in goals if g.status == StatusEnum.COMPLETED]) / max(len(goals), 1) * 100 if goals else 0
            
            prompt = f"""
            Analyze this week's productivity data and provide insights:
            
            Metrics:
            - Average daily task completion: {avg_completion:.1f}
            - Average mood score: {avg_mood:.1f}/10
            - Average energy level: {avg_energy:.1f}/10
            - Average focus score: {avg_focus:.1f}/10
            - Weekly completion rate: {completion_rate:.1f}%
            - Goal progress: {goal_progress:.1f}%
            - Total progress entries: {len(progress_logs)}
            
            Provide analysis in JSON format:
            {{
                "overall_performance": "Excellent/Good/Average/Needs Improvement",
                "key_insights": ["insight1", "insight2", "insight3"],
                "strengths": ["strength1", "strength2"],
                "areas_for_improvement": ["area1", "area2"],
                "recommendations": ["recommendation1", "recommendation2"],
                "productivity_score": 85
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text
            
            analysis = json.loads(json_text)
            # Normalize completion_assessment to expected labels
            if isinstance(analysis, dict) and "completion_assessment" in analysis:
                raw = str(analysis.get("completion_assessment", "")).lower()
                if "ahead" in raw:
                    analysis["completion_assessment"] = "Ahead"
                elif "on track" in raw or "ontrack" in raw:
                    analysis["completion_assessment"] = "On Track"
                elif "behind" in raw:
                    analysis["completion_assessment"] = "Behind"
            return analysis
            
        except Exception as e:
            return {
                "overall_performance": "Good",
                "key_insights": ["You're maintaining consistent progress", "Focus on completing planned tasks"],
                "strengths": ["Regular logging", "Goal-oriented approach"],
                "areas_for_improvement": ["Task completion rate", "Energy management"],
                "recommendations": ["Break large tasks into smaller ones", "Align tasks with your energy levels"],
                "productivity_score": 75
            }

    async def evaluate_phase_transition(self, user: User, goals: List[Goal], time_in_phase_days: int) -> Dict[str, Any]:
        """
        AI Agent 5: Phase Transition Evaluator
        Evaluate readiness for moving to the next entrepreneurial phase.
        """
        try:
            completed_goals = len([g for g in goals if g.status == StatusEnum.COMPLETED])
            total_goals = len(goals)
            completion_rate = (completed_goals / max(total_goals, 1)) * 100
            
            current_phase = user.current_phase
            next_phase_map = {
                "Research": "MVP",
                "MVP": "Growth", 
                "Growth": "Scale",
                "Scale": "Transition"
            }
            next_phase = next_phase_map.get(current_phase, "Advanced")
            
            prompt = f"""
            Evaluate phase transition readiness for an entrepreneur:
            
            Current Phase: {current_phase}
            Phase Duration: {time_in_phase_days} days
            Goal Completion Rate: {completion_rate:.1f}%
            Completed Goals: {completed_goals}/{total_goals}
            Target Quit Date: {user.quit_job_target}
            
            Provide evaluation in JSON format:
            {{
                "current_phase": "{current_phase}",
                "next_phase": "{next_phase}",
                "readiness_score": 85,
                "recommendation": "Go/Wait/Pivot",
                "key_achievements": ["achievement1", "achievement2"],
                "blockers": ["blocker1", "blocker2"],
                "next_steps": ["step1", "step2", "step3"],
                "timeline_estimate": "2-4 weeks"
            }}
            
            Consider typical phase requirements:
            - Research: Market validation, problem identification
            - MVP: Product development, initial user feedback
            - Growth: User acquisition, revenue generation
            - Scale: Team building, process optimization
            - Transition: Financial stability, sustainable revenue
            """
            
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text
            
            evaluation = json.loads(json_text)
            return evaluation
            
        except Exception as e:
            return {
                "current_phase": current_phase,
                "next_phase": next_phase,
                "readiness_score": 70,
                "recommendation": "Wait",
                "key_achievements": ["Consistent progress tracking", "Goal setting"],
                "blockers": ["Need more goal completion", "Require market validation"],
                "next_steps": ["Complete current phase goals", "Gather user feedback", "Validate assumptions"],
                "timeline_estimate": "4-6 weeks"
            }

    async def analyze_career_transition_readiness(self, user: User, job_metrics: JobMetrics) -> Dict[str, Any]:
        """
        AI Agent 6: Career Transition Decision AI
        Analyze financial and personal readiness for career transition.
        """
        try:
            # Calculate financial metrics
            monthly_salary = float(job_metrics.current_salary / 12) if job_metrics.current_salary else 0
            monthly_revenue = float(job_metrics.startup_revenue) if job_metrics.startup_revenue else 0
            monthly_expenses = float(job_metrics.monthly_expenses) if job_metrics.monthly_expenses else 0
            
            revenue_replacement_ratio = (monthly_revenue / monthly_salary * 100) if monthly_salary > 0 else 0
            runway_months = job_metrics.runway_months or 0
            
            prompt = f"""
            Analyze career transition readiness:
            
            Financial Metrics:
            - Monthly Salary: ${monthly_salary:,.2f}
            - Monthly Startup Revenue: ${monthly_revenue:,.2f}
            - Monthly Expenses: ${monthly_expenses:,.2f}
            - Revenue Replacement Ratio: {revenue_replacement_ratio:.1f}%
            - Runway Months: {runway_months:.1f}
            - Quit Readiness Score: {job_metrics.quit_readiness_score or 0:.1f}%
            
            Personal Metrics:
            - Current Phase: {user.current_phase}
            - Stress Level: {job_metrics.stress_level}/10
            - Job Satisfaction: {job_metrics.job_satisfaction}/10
            - Target Quit Date: {user.quit_job_target}
            
            Provide analysis in JSON format:
            {{
                "financial_readiness": "High/Medium/Low",
                "personal_readiness": "High/Medium/Low", 
                "overall_recommendation": "Ready/Wait/Not Ready",
                "risk_level": "Low/Medium/High",
                "key_strengths": ["strength1", "strength2"],
                "concerns": ["concern1", "concern2"],
                "action_items": ["action1", "action2", "action3"],
                "timeline_recommendation": "Immediate/3-6 months/6-12 months",
                "confidence_score": 85
            }}
            
            Consider:
            - 50%+ revenue replacement is good, 100%+ is excellent
            - 6+ months runway is recommended
            - High stress + low satisfaction supports transition
            - Current business phase impacts timing
            """
            
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text
            
            analysis = json.loads(json_text)
            return analysis
            
        except Exception as e:
            # Determine basic risk level
            if revenue_replacement_ratio >= 50 and runway_months >= 6:
                risk_level = "Low"
                recommendation = "Ready"
            elif revenue_replacement_ratio >= 25 and runway_months >= 3:
                risk_level = "Medium" 
                recommendation = "Wait"
            else:
                risk_level = "High"
                recommendation = "Not Ready"
            
            return {
                "financial_readiness": "Medium",
                "personal_readiness": "Medium",
                "overall_recommendation": recommendation,
                "risk_level": risk_level,
                "key_strengths": ["Progress tracking", "Goal-oriented approach"],
                "concerns": ["Revenue needs improvement", "Build larger financial buffer"],
                "action_items": ["Increase monthly revenue", "Reduce expenses", "Build emergency fund"],
                "timeline_recommendation": "6-12 months",
                "confidence_score": 70
            }

    async def analyze_goals(self, goals: List[Goal], progress_logs: Optional[List[ProgressLog]] = None) -> Dict[str, Any]:
        """
        AI Agent 7: Goals Analysis Intelligence
        Analyze goals progress, patterns, and provide strategic insights for goal achievement.
        """
        try:
            # Calculate goal metrics
            total_goals = len(goals)
            completed_goals = len([g for g in goals if g.status == StatusEnum.COMPLETED])
            in_progress_goals = len([g for g in goals if g.status == StatusEnum.ACTIVE])
            paused_goals = len([g for g in goals if g.status == StatusEnum.PAUSED])
            completion_rate = (completed_goals / max(total_goals, 1)) * 100

            # Calculate average completion percentage for in-progress goals
            active_goals_completion = [g.completion_percentage for g in goals if g.status == StatusEnum.ACTIVE]
            avg_completion_percentage = sum(active_goals_completion) / max(len(active_goals_completion), 1) if active_goals_completion else 0

            # Analyze progress patterns if logs are provided
            progress_trend = "steady"
            if progress_logs:
                recent_logs = sorted(progress_logs, key=lambda x: x.created_at)[-7:]  # Last 7 logs
                if recent_logs:
                    start_completion = recent_logs[0].tasks_completed
                    end_completion = recent_logs[-1].tasks_completed
                    progress_trend = "improving" if end_completion > start_completion else "declining" if end_completion < start_completion else "steady"

            # Prepare goals context for analysis
            goals_context = []
            for goal in goals:
                goals_context.append({
                    "description": goal.description,
                    "priority": goal.priority.value,
                    "completion": f"{goal.completion_percentage}%",
                    "phase": goal.phase.value,
                    "status": goal.status.value,
                    "created_at": goal.created_at.isoformat() if goal.created_at else None
                })

            prompt = f"""
            Analyze entrepreneurial goals and provide strategic insights:

            Goal Metrics:
            - Total Goals: {total_goals}
            - Completed: {completed_goals}
            - In Progress: {in_progress_goals}
            - Paused: {paused_goals}
            - Overall Completion Rate: {completion_rate:.1f}%
            - Avg Progress on Active Goals: {avg_completion_percentage:.1f}%
            - Progress Trend: {progress_trend}

            Goals Details:
            {json.dumps(goals_context, indent=2)}

            Provide analysis in JSON format:
            {{
                "overall_status": "Excellent/Good/Average/Needs Attention",
                "completion_assessment": "Ahead/On Track/Behind",
                "key_insights": ["insight1", "insight2", "insight3"],
                "success_patterns": ["pattern1", "pattern2"],
                "challenges": ["challenge1", "challenge2"],
                "recommendations": ["recommendation1", "recommendation2", "recommendation3"],
                "priority_adjustments": ["adjustment1", "adjustment2"],
                "achievement_score": 85,
                "focus_areas": ["area1", "area2"]
            }}

            Consider:
            - Goal dependencies and sequencing
            - Balance between short and long-term goals
            - Resource allocation and priority alignment
            - Progress velocity and momentum
            - Risk factors and mitigation strategies
            """

            response = self.model.generate_content(prompt)

            # Extract JSON from response
            response_text = response.text.strip()
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text

            analysis = json.loads(json_text)
            return analysis

        except Exception as e:
            # Calculate basic metrics even in error case
            total_goals = len(goals)
            completed_goals = len([g for g in goals if g.status == StatusEnum.COMPLETED])
            in_progress_goals = len([g for g in goals if g.status == StatusEnum.ACTIVE])
            completion_rate = (completed_goals / max(total_goals, 1)) * 100
            active_goals_completion = [g.completion_percentage for g in goals if g.status == StatusEnum.ACTIVE]
            avg_completion_percentage = sum(active_goals_completion) / max(len(active_goals_completion), 1) if active_goals_completion else 0

            # Provide fallback analysis
            if total_goals == 0:
                return {
                    "overall_status": "Average",
                    "completion_assessment": "On Track",
                    "key_insights": ["No goals", "Progress tracking requires goals"],
                    "success_patterns": ["Consistent tracking", "Regular planning"],
                    "challenges": ["Need more progress data"],
                    "recommendations": ["Start setting goals", "Begin tracking daily progress"],
                    "priority_adjustments": ["Review goal priorities"],
                    "achievement_score": 65,
                    "focus_areas": ["Progress tracking", "Goal completion"]
                }

            # Calculate status based on completion rate and active goals
            status = "Good" if completion_rate >= 50 or (in_progress_goals > 0 and avg_completion_percentage >= 60) else "Average" if completion_rate >= 30 or in_progress_goals > 0 else "Needs Attention"
            assessment = "Ahead" if completion_rate >= 80 else "On Track" if completion_rate >= 50 or (in_progress_goals > 0 and avg_completion_percentage >= 50) else "Behind"
            
            return {
                "overall_status": status,
                "completion_assessment": assessment,
                "key_insights": [
                    "Regular goal tracking is maintained",
                    f"{completed_goals} of {total_goals} goals completed",
                    f"{in_progress_goals} goals actively in progress"
                ],
                "success_patterns": [
                    "Consistent goal setting",
                    "Regular progress tracking"
                ],
                "challenges": [
                    "Some goals need more progress",
                    "Need to maintain momentum"
                ],
                "recommendations": [
                    "Focus on completing in-progress goals",
                    "Review and update goal priorities",
                    "Break down larger goals into smaller milestones"
                ],
                "priority_adjustments": ["Balance workload across goals"],
                "achievement_score": int(completion_rate),
                "focus_areas": ["Goal completion", "Progress tracking"]
            }

    async def generate_progress_log_content(
        self,
        session: Session,
        user_id: str,
        date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        AI Agent 8: Progress Log Generator
        Generate a comprehensive progress log based on user's activities, tasks, and metrics for a given day.
        """
        try:
            # Use today's date if not specified
            target_date = date or datetime.utcnow().date()

            # Day boundaries
            day_start = datetime.combine(target_date, datetime.min.time())
            next_day_start = datetime.combine(target_date + timedelta(days=1), datetime.min.time())

            # Optional DayLog record for narrative and environment context
            day_log = session.exec(
                select(DayLog).where(DayLog.user_id == user_id, DayLog.date == target_date)
            ).first()

            # Get tasks completed or worked on today
            tasks = session.exec(
                select(Task).where(
                    Task.user_id == user_id,
                    Task.updated_at >= day_start,
                    Task.updated_at < next_day_start,
                )
            ).all()

            # There is no user association on Log; omit logs from context
            logs: List[Log] = []

            # Get latest job metrics
            job_metrics = session.exec(
                select(JobMetrics)
                .where(JobMetrics.user_id == user_id)
                .order_by(JobMetrics.created_at.desc())
            ).first()

            # Progress log for mood/energy on the target date
            progress_entry = session.exec(
                select(ProgressLog).where(
                    ProgressLog.user_id == user_id, ProgressLog.date == target_date
                )
            ).first()

            # Prepare context for AI
            completed_tasks = [t for t in tasks if t.completion_status == CompletionStatusEnum.COMPLETED]
            in_progress_tasks = [t for t in tasks if t.completion_status == CompletionStatusEnum.IN_PROGRESS]

            # Prepare DayLog context if available
            day_log_context = None
            if day_log:
                # Compute duration in hours if both timestamps present
                duration_hours = None
                if day_log.start_time and day_log.end_time:
                    try:
                        duration_hours = (
                            (day_log.end_time - day_log.start_time).total_seconds() / 3600.0
                        )
                    except Exception:
                        duration_hours = None
                day_log_context = {
                    "summary": day_log.summary,
                    "highlights": day_log.highlights,
                    "challenges": day_log.challenges,
                    "learnings": day_log.learnings,
                    "gratitude": day_log.gratitude,
                    "tomorrow_plan": day_log.tomorrow_plan,
                    "weather": day_log.weather,
                    "location": day_log.location,
                    "start_time": day_log.start_time.isoformat() if day_log.start_time else None,
                    "end_time": day_log.end_time.isoformat() if day_log.end_time else None,
                    "duration_hours": duration_hours,
                }

            context = {
                "day_summary": {
                    "mood": (progress_entry.mood_score if progress_entry else None),
                    "energy_level": (progress_entry.energy_level if progress_entry else None),
                    "sleep_quality": None,
                },
                "tasks": {
                    "completed": [t.description for t in completed_tasks],
                    "in_progress": [t.description for t in in_progress_tasks],
                },
                "logs": [],
                "metrics": {
                    "productivity": None,
                    "stress_level": (job_metrics.stress_level if job_metrics else None),
                },
                "day_log": day_log_context,
            }
            
            prompt = f"""
            Generate a comprehensive progress log based on today's activities:
            
            Context:
            {json.dumps(context, indent=2)}
            
            Generate a progress log in JSON format:
            {{
                "achievements": ["achievement1", "achievement2"],
                "challenges": ["challenge1", "challenge2"],
                "learnings": ["learning1", "learning2"],
                "next_steps": ["step1", "step2"],
                "mood_analysis": "Analysis of mood and energy impact",
                "productivity_insights": "Analysis of productivity patterns"
            }}
            
            Guidelines:
            - Extract achievements from completed tasks and logs
            - Identify challenges from in-progress tasks and mood
            - Derive learnings from the day's experiences
            - Suggest next steps based on current progress
            - Analyze mood and energy impact on productivity
            - Provide actionable productivity insights
            """
            
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text
            
            progress_data = json.loads(json_text)
            return progress_data
            
        except Exception as e:
            # Provide a basic fallback response
            return {
                "achievements": ["Tracked daily progress", "Maintained activity log"],
                "challenges": ["Some tasks still in progress", "Need to improve tracking"],
                "learnings": ["Regular tracking helps progress", "Important to maintain logs"],
                "next_steps": ["Complete pending tasks", "Continue progress tracking"],
                "mood_analysis": "Consistent tracking of daily activities",
                "productivity_insights": "Regular logging supports productivity"
            }

    async def generate_day_log_content(
        self,
        session: Session,
        user_id: str,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        AI Agent 9: Day Log Generator
        Generate day log narrative sections (summary, highlights, challenges, learnings, gratitude, tomorrow_plan)
        using user's tasks and notes for the given day.
        """
        try:
            day_date = target_date or datetime.utcnow().date()

            # Gather context for the day
            start = datetime.combine(day_date, datetime.min.time())
            end = datetime.combine(day_date + timedelta(days=1), datetime.min.time())

            tasks = session.exec(
                select(Task).where(
                    Task.user_id == user_id,
                    Task.updated_at >= start,
                    Task.updated_at < end,
                )
            ).all()

            # No user association on Log; omit notes
            notes: List[Log] = []

            completed = [t.description for t in tasks if getattr(t, "completion_status", None) == CompletionStatusEnum.COMPLETED]
            in_progress = [t.description for t in tasks if getattr(t, "completion_status", None) == CompletionStatusEnum.IN_PROGRESS]

            context = {
                "date": str(day_date),
                "tasks": {
                    "completed": completed,
                    "in_progress": in_progress,
                },
                "notes": [],
            }

            prompt = f"""
            You are a helpful productivity assistant. Create a concise day log for the user based on the context.

            Context (JSON):
            {json.dumps(context, indent=2)}

            Return a JSON object with these fields only:
            {{
              "summary": "1-2 sentence overview of the day",
              "highlights": "bullet-style text capturing wins",
              "challenges": "bullet-style text capturing blockers",
              "learnings": "bullet-style text capturing learning",
              "gratitude": "one short sentence",
              "tomorrow_plan": "bullet-style text for next steps"
            }}
            """

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text

            data = json.loads(json_text)
            return data
        except Exception:
            # Sensible fallback if AI unavailable
            return {
                "summary": "Tracked tasks and made steady progress.",
                "highlights": "- Advanced key tasks\n- Maintained momentum",
                "challenges": "- Some tasks remained in progress",
                "learnings": "- Small consistent steps compound",
                "gratitude": "Grateful for the ability to keep moving forward.",
                "tomorrow_plan": "- Pick up remaining tasks\n- Plan one quick win early"
            }

    async def generate_job_metrics_for_user(
        self,
        session: Session,
        user_id: str
    ) -> Dict[str, Any]:
        """
        AI Agent 10: Job Metrics Generator
        Estimate or synthesize job metrics fields from recent activity context.
        Returns a dict suitable to construct a JobMetrics model.
        """
        try:
            # Collect very lightweight context for AI prompt (recent tasks / logs counts)
            today = datetime.utcnow().date()
            start = datetime.combine(today - timedelta(days=7), datetime.min.time())
            end = datetime.combine(today + timedelta(days=1), datetime.min.time())

            recent_tasks = session.exec(
                select(Task).where(
                    Task.user_id == user_id,
                    Task.updated_at >= start,
                    Task.updated_at < end,
                )
            ).all()
            completed = len([t for t in recent_tasks if getattr(t, "completion_status", None) == CompletionStatusEnum.COMPLETED])
            total = len(recent_tasks)

            # No user association on Log; set to 0
            notes_count = 0

            context = {
                "recent_tasks_total": total,
                "recent_tasks_completed": completed,
                "recent_notes": notes_count,
            }

            prompt = f"""
            Based on the recent productivity context below, estimate reasonable values for job metrics.
            Context (JSON): {json.dumps(context)}

            Return a JSON object with numeric values only for these keys.
            If you don't know, return mid-range sensible defaults:
            {{
              "stress_level": 1-10 integer,
              "job_satisfaction": 1-10 integer,
              "startup_revenue": number or null,
              "current_salary": number or null,
              "monthly_expenses": number or null,
              "runway_months": number or null,
              "quit_readiness_score": number between 0 and 100
            }}
            """

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text

            data = json.loads(json_text)
            # Ensure required fields exist
            data.setdefault("stress_level", 5)
            data.setdefault("job_satisfaction", 5)
            data.setdefault("quit_readiness_score", 0)
            return data
        except Exception:
            return {
                "stress_level": 5,
                "job_satisfaction": 5,
                "startup_revenue": None,
                "current_salary": None,
                "monthly_expenses": None,
                "runway_months": None,
                "quit_readiness_score": 0,
            }