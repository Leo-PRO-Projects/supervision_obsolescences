from __future__ import annotations

from datetime import date
from typing import Dict, List

from pydantic import BaseModel


class ObsolescenceBucket(BaseModel):
    label: str
    count: int


class RemediationStats(BaseModel):
    status: str
    count: int


class ProjectCriticityStat(BaseModel):
    project: str
    criticity: str
    count: int


class DependencyAlert(BaseModel):
    dependency_name: str
    shared_by: List[str]
    end_of_support: date | None
    urgency_color: str


class DashboardMetrics(BaseModel):
    total_items: int
    obsolete_count: int
    expiring_soon: Dict[str, int]
    remediation_stats: List[RemediationStats]
    timeline_histogram: Dict[str, int]
    project_criticity: List[ProjectCriticityStat]
    shared_dependency_alerts: List[DependencyAlert]
    top_priorities: List[Dict[str, str]]
