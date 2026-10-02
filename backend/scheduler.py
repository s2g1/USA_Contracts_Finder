import asyncio
import logging
from datetime import datetime
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.config import settings
from backend.sam_client import sam_client
from backend.scoring_engine import scoring_engine
from backend.database import upsert_solicitation, save_scorecard, log_sync, get_latest_sync_log

logger = logging.getLogger(__name__)

class SyncScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.timezone = pytz.timezone(settings.SCHEDULE_TIMEZONE)
        self.is_running_sync = False

    def start(self):
        # Configure daily cron trigger at 5:00 PM EST (17:00)
        trigger = CronTrigger(
            hour=settings.SCHEDULE_HOUR,
            minute=settings.SCHEDULE_MINUTE,
            timezone=self.timezone
        )
        self.scheduler.add_job(
            self.run_scheduled_sync,
            trigger=trigger,
            id="daily_sam_sync",
            name="Daily SAM.gov Solicitations Sync",
            replace_existing=True
        )
        self.scheduler.start()
        logger.info(f"Daily SAM.gov scheduler started. Scheduled for {settings.SCHEDULE_HOUR:02d}:{settings.SCHEDULE_MINUTE:02d} {settings.SCHEDULE_TIMEZONE}.")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()

    async def run_scheduled_sync(self):
        logger.info("Executing scheduled SAM.gov solicitation query (5:00 PM EST)...")
        await self.execute_sync(source="SCHEDULED_CRON")

    async def execute_sync(self, source: str = "MANUAL_TRIGGER", days_back: int = 1) -> dict:
        if self.is_running_sync:
            return {"status": "IN_PROGRESS", "message": "A sync is already in progress"}

        self.is_running_sync = True
        new_count = 0
        updated_count = 0
        found_count = 0
        status = "SUCCESS"
        message = ""

        try:
            logger.info(f"Starting solicitation sync from source: {source}")
            # Ensure skills engine has latest config
            scoring_engine.reload()

            opportunities, fetch_status = await sam_client.fetch_opportunities(days_back=days_back)
            found_count = len(opportunities)

            for opp in opportunities:
                # 1. Upsert into database
                is_new, is_updated = upsert_solicitation(opp)
                if is_new:
                    new_count += 1
                elif is_updated:
                    updated_count += 1

                # 2. Perform scorecard calculations based on skill sets file
                scorecard = scoring_engine.calculate_scorecard(opp)

                # 3. Store scorecard in database
                save_scorecard(scorecard)

            message = f"{fetch_status}. Processed {found_count} solicitations ({new_count} new, {updated_count} updated)."
            logger.info(f"Sync complete: {message}")

        except Exception as e:
            status = "FAILED"
            message = f"Error during sync: {str(e)}"
            logger.exception("Sync execution failed")
        finally:
            log_sync(
                source=source,
                found_count=found_count,
                new_count=new_count,
                updated_count=updated_count,
                status=status,
                message=message
            )
            self.is_running_sync = False

        return {
            "source": source,
            "status": status,
            "found_count": found_count,
            "new_count": new_count,
            "updated_count": updated_count,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_schedule_info(self) -> dict:
        job = self.scheduler.get_job("daily_sam_sync")
        next_run_time = job.next_run_time if job else None

        time_until = None
        if next_run_time:
            now_tz = datetime.now(self.timezone)
            time_until = max(0, int((next_run_time - now_tz).total_seconds()))

        latest_log = get_latest_sync_log()

        return {
            "schedule": f"{settings.SCHEDULE_HOUR:02d}:{settings.SCHEDULE_MINUTE:02d} {settings.SCHEDULE_TIMEZONE}",
            "next_run_time": next_run_time.isoformat() if next_run_time else None,
            "seconds_until_next_run": time_until,
            "is_running_sync": self.is_running_sync,
            "latest_sync": latest_log,
            "timezone": settings.SCHEDULE_TIMEZONE
        }

sync_scheduler = SyncScheduler()
