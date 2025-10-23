from __future__ import annotations

import csv
import io
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.api.routes.applications import apply_filters
from app.core.database import get_db
from app.models.entities import Application, UserRole
from app.services.importer import CSVImportService, CSV_HEADERS

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/template")
async def download_template(
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> StreamingResponse:
    service = CSVImportService(db)
    content = service.generate_template()
    return StreamingResponse(io.BytesIO(content), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=inventory_template.csv"})


@router.post("/import", status_code=status.HTTP_202_ACCEPTED)
async def import_inventory(
    file: UploadFile,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> dict[str, int]:
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seuls les fichiers CSV sont supportés")
    service = CSVImportService(db)
    return service.import_csv(file)


@router.get("/export")
async def export_inventory(
    project_id: Optional[int] = None,
    criticity: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    __: None = Depends(get_current_user),
) -> StreamingResponse:
    query = db.query(Application)
    query = apply_filters(query, project_id, criticity, status_filter, search)
    applications: List[Application] = query.all()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_HEADERS)
    writer.writeheader()
    for app in applications:
        base_row = {
            "project_name": app.project.name if app.project else "",
            "project_team": app.project.team if app.project else "",
            "project_contact": app.project.contact if app.project else "",
            "application_name": app.name,
            "application_description": app.description,
            "application_owner": app.owner,
            "application_criticity": app.criticity.value,
            "application_status": app.status.value,
        }
        if not app.versions and not app.dependencies:
            writer.writerow(base_row)
        for version in app.versions or [None]:
            for dependency in app.dependencies or [None]:
                row = base_row.copy()
                if version:
                    row.update(
                        {
                            "version_number": version.number,
                            "version_end_of_support": version.end_of_support.isoformat() if version.end_of_support else "",
                            "version_end_of_contract": version.end_of_contract.isoformat() if version.end_of_contract else "",
                        }
                    )
                if dependency:
                    row.update(
                        {
                            "dependency_category": dependency.category.value,
                            "dependency_name": dependency.name,
                            "dependency_version": dependency.version,
                            "dependency_end_of_support": dependency.end_of_support.isoformat()
                            if dependency.end_of_support
                            else "",
                        }
                    )
                writer.writerow(row)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventory_export.csv"},
    )
