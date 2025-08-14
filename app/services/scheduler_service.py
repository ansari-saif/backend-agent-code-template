from typing import Callable, Optional
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


class SchedulerService:
    """Thin wrapper around AsyncIOScheduler to manage background jobs.

    The scheduler is started conditionally based on ENABLE_SCHEDULER env var to
    avoid interfering with tests. Timezone defaults to Asia/Kolkata respecting
    user preference for IST.
    """

    def __init__(self, timezone: str = "Asia/Kolkata") -> None:
        self._timezone = timezone
        self.scheduler = AsyncIOScheduler(timezone=timezone)

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()

    def add_cron_job(self, func: Callable, *, id: Optional[str] = None, **cron_kwargs):
        trigger = CronTrigger(**cron_kwargs)
        return self.scheduler.add_job(func, trigger, id=id, replace_existing=True)


