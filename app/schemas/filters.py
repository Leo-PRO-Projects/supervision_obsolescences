from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


class ApplicationFilter(BaseModel):
    project_id: Optional[int]
    criticity: Optional[str]
    status: Optional[str]
    search: Optional[str]


class DashboardFilter(BaseModel):
    project_id: Optional[int]
    criticity: Optional[str]
    technology: Optional[str]
    deadline_before: Optional[date]
