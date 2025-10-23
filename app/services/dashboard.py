from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.entities import (
    Application,
    Dependency,
    Project,
    RemediationStatus,
    Version,
)
from app.schemas.dashboard import DashboardMetrics, DependencyAlert, ProjectCriticityStat, RemediationStats


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def _deadline_bucket(self, deadline: date | None) -> str:
        if not deadline:
            return "> 6 mois"
        today = date.today()
        delta_months = (deadline.year - today.year) * 12 + (deadline.month - today.month)
        if delta_months <= 0:
            return "Obsolète"
        if delta_months <= 3:
            return "< 3 mois"
        if delta_months <= 6:
            return "3-6 mois"
        return "> 6 mois"

    def get_metrics(self) -> DashboardMetrics:
        today = date.today()
        total_versions = self.db.query(func.count(Version.id)).scalar() or 0
        total_dependencies = self.db.query(func.count(Dependency.id)).scalar() or 0
        total_items = total_versions + total_dependencies

        obsolete_versions = (
            self.db.query(Version).filter(Version.end_of_support.isnot(None), Version.end_of_support < today).count()
        )
        obsolete_dependencies = (
            self.db.query(Dependency)
            .filter(Dependency.end_of_support.isnot(None), Dependency.end_of_support < today)
            .count()
        )
        obsolete_count = obsolete_versions + obsolete_dependencies

        expiring_counter = Counter({"< 3 mois": 0, "3-6 mois": 0, "> 6 mois": 0, "Obsolète": 0})

        for version in self.db.query(Version).filter(Version.end_of_support.isnot(None)).all():
            bucket = self._deadline_bucket(version.end_of_support)
            expiring_counter[bucket] += 1
        for dependency in self.db.query(Dependency).filter(Dependency.end_of_support.isnot(None)).all():
            bucket = self._deadline_bucket(dependency.end_of_support)
            expiring_counter[bucket] += 1

        expiring_counter["Obsolète"] = obsolete_count

        remediation_stats = [
            RemediationStats(status=status.value, count=self.db.query(Version).filter(Version.remediation_status == status).count())
            for status in RemediationStatus
        ]

        timeline_histogram: Dict[str, int] = {}
        for version in self.db.query(Version).filter(Version.end_of_support.isnot(None)).all():
            eos = version.end_of_support
            period = f"{eos.year}-T{((eos.month - 1) // 3) + 1}"
            timeline_histogram[period] = timeline_histogram.get(period, 0) + 1

        project_stats_query = (
            self.db.query(Project.name, Application.criticity, func.count(Application.id))
            .join(Project, Application.project_id == Project.id)
            .group_by(Project.name, Application.criticity)
            .all()
        )
        project_criticity: List[ProjectCriticityStat] = []
        for project_name, criticity, count in project_stats_query:
            project_criticity.append(
                ProjectCriticityStat(project=project_name, criticity=criticity.value if hasattr(criticity, "value") else criticity, count=count)
            )

        dependency_alerts: List[DependencyAlert] = []
        dependency_groups = defaultdict(list)
        for dependency in self.db.query(Dependency).filter(Dependency.end_of_support.isnot(None)).all():
            key = (dependency.name, dependency.end_of_support)
            dependency_groups[key].append(dependency.application.name if dependency.application else "")
        for (name, eos), apps in dependency_groups.items():
            if len(apps) < 2:
                continue
            bucket = self._deadline_bucket(eos)
            color = {"< 3 mois": "red", "3-6 mois": "orange", "> 6 mois": "green", "Obsolète": "red"}.get(bucket, "grey")
            dependency_alerts.append(
                DependencyAlert(
                    dependency_name=name,
                    shared_by=apps,
                    end_of_support=eos,
                    urgency_color=color,
                )
            )

        top_items: List[dict[str, str]] = []
        for version in (
            self.db.query(Version)
            .filter(Version.end_of_support.isnot(None))
            .order_by(Version.end_of_support)
            .limit(10)
            .all()
        ):
            top_items.append(
                {
                    "type": "version",
                    "application": version.application.name if version.application else "",
                    "label": version.number,
                    "deadline": version.end_of_support.isoformat() if version.end_of_support else "",
                    "criticity": version.application.criticity.value if version.application else "",
                }
            )
        for dependency in (
            self.db.query(Dependency)
            .filter(Dependency.end_of_support.isnot(None))
            .order_by(Dependency.end_of_support)
            .limit(10)
            .all()
        ):
            top_items.append(
                {
                    "type": "dependency",
                    "application": dependency.application.name if dependency.application else "",
                    "label": dependency.name,
                    "deadline": dependency.end_of_support.isoformat() if dependency.end_of_support else "",
                    "criticity": dependency.application.criticity.value if dependency.application else "",
                }
            )
        top_items = sorted(top_items, key=lambda item: item.get("deadline") or "")[:10]

        return DashboardMetrics(
            total_items=total_items,
            obsolete_count=obsolete_count,
            expiring_soon=dict(expiring_counter),
            remediation_stats=remediation_stats,
            timeline_histogram=timeline_histogram,
            project_criticity=project_criticity,
            shared_dependency_alerts=dependency_alerts,
            top_priorities=top_items,
        )
