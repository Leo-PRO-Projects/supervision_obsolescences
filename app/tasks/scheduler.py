from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.entities import Application
from app.services.notifications import NotificationService, format_notification_html

logger = logging.getLogger(__name__)
settings = get_settings()


def notify_upcoming_obsolescences() -> None:
    with SessionLocal() as session:
        service = NotificationService(session)
        records = service.upcoming_obsolescences(settings.alert_threshold_months)
        for application, version, dependency in records:
            recipients = []
            if application.owner:
                recipients.append(application.owner)
            if application.project and application.project.contact:
                recipients.append(application.project.contact)
            if not recipients:
                continue
            subject = f"[Obsolescences] {application.name}"
            body = format_notification_html(application, version, dependency)
            try:
                service.send_email_notification("application", application.id, recipients, subject, body)
                logger.info("Notification envoyée pour %s", application.name)
            except Exception as exc:  # pragma: no cover - logged by service
                logger.warning("Échec notification %s: %s", application.name, exc)


def start_scheduler(app: FastAPI) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
    scheduler.add_job(notify_upcoming_obsolescences, CronTrigger(hour=7, minute=0))

    @app.on_event("startup")
    async def start() -> None:  # pragma: no cover - scheduler start
        if settings.scheduler_enabled:
            scheduler.start()
            logger.info("Planificateur démarré")

    @app.on_event("shutdown")
    async def shutdown() -> None:  # pragma: no cover - scheduler shutdown
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("Planificateur arrêté")

    return scheduler
