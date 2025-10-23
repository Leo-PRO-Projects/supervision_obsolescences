from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Iterable, List, Optional

import requests
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models.entities import Application, Dependency, Notification, NotificationType, Version

logger = logging.getLogger(__name__)
settings = get_settings()


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def _send_email(self, recipients: Iterable[str], subject: str, body: str) -> str:
        if not settings.smtp_host or not settings.smtp_sender:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SMTP non configuré",
            )
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.smtp_sender
        message["To"] = ", ".join(recipients)
        message.set_content(body, subtype="html")
        import smtplib

        try:
            if settings.smtp_use_tls:
                with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                    server.starttls()
                    if settings.smtp_user and settings.smtp_password:
                        server.login(settings.smtp_user, settings.smtp_password)
                    server.send_message(message)
            else:
                with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                    if settings.smtp_user and settings.smtp_password:
                        server.login(settings.smtp_user, settings.smtp_password)
                    server.send_message(message)
            return "sent"
        except smtplib.SMTPException as exc:  # type: ignore[attr-defined]
            logger.exception("Erreur d'envoi SMTP")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Envoi SMTP échoué") from exc

    def _send_teams(self, summary: str) -> str:
        if not settings.teams_webhook_url:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Webhook Teams non configuré")
        payload = {"text": summary}
        try:
            response = requests.post(settings.teams_webhook_url, json=payload, timeout=10)
        except requests.RequestException as exc:
            logger.exception("Erreur de connexion au webhook Teams")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Connexion Teams échouée") from exc
        if response.status_code >= 400:
            logger.error("Erreur webhook Teams: %s - %s", response.status_code, response.text)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Webhook Teams échoué")
        return "sent"

    def log_notification(
        self,
        target_type: str,
        target_id: int,
        type_: NotificationType,
        recipients: Iterable[str],
        status_msg: str,
        message: str,
    ) -> Notification:
        notification = Notification(
            target_type=target_type,
            target_id=target_id,
            type=type_,
            recipients=", ".join(recipients),
            status=status_msg,
            message=message,
            sent_at=datetime.now(timezone.utc),
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def send_email_notification(
        self,
        target_type: str,
        target_id: int,
        recipients: Iterable[str],
        subject: str,
        body: str,
    ) -> Notification:
        status_msg = self._send_email(recipients, subject, body)
        return self.log_notification(target_type, target_id, NotificationType.email, recipients, status_msg, body)

    def send_teams_notification(
        self,
        target_type: str,
        target_id: int,
        summary: str,
    ) -> Notification:
        status_msg = self._send_teams(summary)
        return self.log_notification(target_type, target_id, NotificationType.teams, ["teams"], status_msg, summary)

    def upcoming_obsolescences(self, within_months: int) -> List[tuple[Application, Optional[Version], Optional[Dependency]]]:
        today = date.today()
        threshold_date = today + timedelta(days=30 * within_months)
        versions = (
            self.db.query(Version)
            .options(joinedload(Version.application).joinedload(Application.project))
            .filter(Version.end_of_support.isnot(None))
            .filter(Version.end_of_support <= threshold_date)
            .all()
        )
        dependencies = (
            self.db.query(Dependency)
            .options(joinedload(Dependency.application).joinedload(Application.project))
            .filter(Dependency.end_of_support.isnot(None))
            .filter(Dependency.end_of_support <= threshold_date)
            .all()
        )
        results: List[tuple[Application, Optional[Version], Optional[Dependency]]] = []
        for version in versions:
            results.append((version.application, version, None))
        for dependency in dependencies:
            results.append((dependency.application, None, dependency))
        return results


def format_notification_html(application: Application, version: Optional[Version], dependency: Optional[Dependency]) -> str:
    details = [f"<h3>{application.name}</h3>"]
    details.append(f"<p>Projet: {application.project.name if application.project else 'N/A'}</p>")
    details.append(f"<p>Criticité: {application.criticity.value}</p>")
    if version:
        details.append(
            f"<p>Version {version.number} - Fin de support: {version.end_of_support or 'N/A'} - Statut: {version.remediation_status.value}</p>"
        )
    if dependency:
        details.append(
            f"<p>Dépendance {dependency.name} ({dependency.category.value}) - Fin de support: {dependency.end_of_support or 'N/A'}</p>"
        )
    details.append("<p>Merci de mettre à jour le plan d'action dans l'outil.</p>")
    return "".join(details)
