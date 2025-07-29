import google.generativeai as genai
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from app.models.user import User
from app.models.goal import Goal, StatusEnum
from app.models.task import Task, CompletionStatusEnum
from app.models.progress_log import ProgressLog
from app.models.ai_context import AIContext
from app.models.job_metrics import JobMetrics


class AIService:
    def __init__(self):
        """Initialize the AI service with Gemini API."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    async def create_daily_tasks(self, tasks: str, user: User, recent_progress: List[ProgressLog], pending_goals: List[Goal], today_energy_level: int = 5) -> List[Dict[str, Any]]:
        """
        AI Agent 1: Daily Task Intelligence
        Generate AI-powered daily task recommendations based on user context, goals, and recent progress.
        """
        try:
            # Build context for the AI
            context_parts = [
                f"User Profile: {user.name}, Phase: {user.current_phase}, Energy Profile: {user.energy_profile}",
                f"Today's Energy Level: {today_energy_level}/10",
                f"Morning Time: {user.morning_time}",
            ]
            
            if recent_progress:
                avg_completion = sum(log.tasks_completed for log in recent_progress) / len(recent_progress)
                avg_mood = sum(log.mood_score for log in recent_progress) / len(recent_progress)
                context_parts.append(f"Recent Performance: {avg_completion:.1f} tasks completed daily, Average mood: {avg_mood:.1f}/10")
            
            if pending_goals:
                goals_text = "; ".join([f"Id: {goal.goal_id} - {goal.description} (Priority: {goal.priority})" for goal in pending_goals[:3]])
                context_parts.append(f"Current Goals: {goals_text}")
            
            prompt = f"""
            Based on the following context, generate 3-5 actionable daily tasks for today:
            
            Context: 
            {chr(10).join(context_parts)}
            
            Tasks:
            {tasks}
            
            Requirements:
            - Tasks should align with current goals and user's energy level
            - Include estimated duration in minutes
            - Specify energy requirement (must be exactly one of: "Low", "Medium", "High")
            - Set appropriate priority (must be exactly one of: "Low", "Medium", "High", "Urgent")
            - Set completion_status to exactly "Pending" for new tasks
            - goal_id must be an integer number matching one of the provided goal IDs, or null if not tied to a specific goal
            - Make tasks specific and actionable
            
            Return as JSON array with format:
            
            [{{
                "description": "task description",
                "priority": "High",
                "completion_status": "Pending",
                "actual_duration": null,
                "goal_id": 1,
                "deadline": null,
                "estimated_duration": 90,
                "energy_required": "High"
            }}]
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
            
            tasks = json.loads(json_text)
            
            # Validate and fix task data
            for task in tasks:
                # Ensure completion_status is "Pending"
                task["completion_status"] = "Pending"
                
                # Convert goal_id to int or None
                if task.get("goal_id") and not isinstance(task["goal_id"], int):
                    task["goal_id"] = None
                
                # Ensure actual_duration is None for new tasks
                task["actual_duration"] = None
                
                # Ensure deadline is None if not properly formatted
                if not isinstance(task.get("deadline"), str) or not task["deadline"]:
                    task["deadline"] = None
                    
                # Validate priority
                if task["priority"] not in ["Low", "Medium", "High", "Urgent"]:
                    task["priority"] = "Medium"
                    
                # Validate energy_required
                if task["energy_required"] not in ["Low", "Medium", "High"]:
                    task["energy_required"] = "Medium"
            
            return tasks
            
        except Exception as e:
            # Fallback response
            return [
                {
                    "description": "Review and prioritize today's goals",
                    "estimated_duration": 30,
                    "energy_required": "Low",
                    "priority": "High",
                    "completion_status": "Pending",
                    "actual_duration": None,
                    "goal_id": None,
                    "deadline": None
                },
                {
                    "description": "Work on highest priority project task",
                    "estimated_duration": 120,
                    "energy_required": "High",
                    "priority": "High",
                    "completion_status": "Pending",
                    "actual_duration": None,
                    "goal_id": None,
                    "deadline": None
                }
            ]
    async def generate_daily_tasks(self, user: User, recent_progress: List[ProgressLog], pending_goals: List[Goal], today_energy_level: int = 5) -> List[Dict[str, Any]]:
        """
        AI Agent 1: Daily Task Intelligence
        Generate AI-powered daily task recommendations based on user context, goals, and recent progress.
        """
        try:
            # Build context for the AI
            context_parts = [
                f"User Profile: {user.name}, Phase: {user.current_phase}, Energy Profile: {user.energy_profile}",
                f"Today's Energy Level: {today_energy_level}/10",
                f"Morning Time: {user.morning_time}",
            ]
            
            if recent_progress:
                avg_completion = sum(log.tasks_completed for log in recent_progress) / len(recent_progress)
                avg_mood = sum(log.mood_score for log in recent_progress) / len(recent_progress)
                context_parts.append(f"Recent Performance: {avg_completion:.1f} tasks completed daily, Average mood: {avg_mood:.1f}/10")
            
            if pending_goals:
                goals_text = "; ".join([f"{goal.description} (Priority: {goal.priority})" for goal in pending_goals[:3]])
                context_parts.append(f"Current Goals: {goals_text}")
            
            prompt = f"""
            Based on the following context, generate 3-5 actionable daily tasks for today:
            
            {chr(10).join(context_parts)}
            
            Requirements:
            - Tasks should align with current goals and user's energy level
            - Include estimated duration in minutes
            - Specify energy requirement (Low/Medium/High)
            - Set appropriate priority (Low/Medium/High)
            - Make tasks specific and actionable
            
            Return as JSON array with format:
            [{{"description": "task description", "estimated_duration": 90, "energy_required": "High", "priority": "High"}}]
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
            
            tasks = json.loads(json_text)
            return tasks
            
        except Exception as e:
            # Fallback response
            return [
                {
                    "description": "Review and prioritize today's goals",
                    "estimated_duration": 30,
                    "energy_required": "Low",
                    "priority": "High"
                },
                {
                    "description": "Work on highest priority project task",
                    "estimated_duration": 120,
                    "energy_required": "High",
                    "priority": "High"
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

    async def generate_deadline_reminder(self, task: Task, time_remaining: str, user_pattern: str, stress_level: int, completion_rate: float) -> str:
        """
        AI Agent 3: Smart Deadline Intelligence
        Generate contextual deadline reminders based on user patterns and urgency.
        """
        try:
            prompt = f"""
            Generate a smart deadline reminder for:
            
            Task: {task.description}
            Time Remaining: {time_remaining}
            User Pattern: {user_pattern}
            Current Stress Level: {stress_level}/10
            User's Completion Rate: {completion_rate:.1%}
            Task Priority: {task.priority}
            Estimated Duration: {task.estimated_duration} minutes
            
            Create a reminder that:
            - Adjusts tone based on stress level (gentle if high stress, more direct if low stress)
            - Considers user's completion patterns
            - Provides helpful time management suggestions
            - Maintains motivation while being realistic about urgency
            - Includes specific next steps
            
            Keep it concise and actionable.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            urgency = "urgent" if "day" in time_remaining.lower() else "upcoming"
            return f"Friendly reminder: '{task.description}' is {urgency} with {time_remaining} remaining. Consider breaking it into smaller steps if it feels overwhelming!"

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