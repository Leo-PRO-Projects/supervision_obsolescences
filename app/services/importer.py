from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.entities import Application, Dependency, DependencyCategory, Project, Version

logger = logging.getLogger(__name__)

CSV_HEADERS = [
    "project_name",
    "project_team",
    "project_contact",
    "application_name",
    "application_description",
    "application_owner",
    "application_criticity",
    "application_status",
    "version_number",
    "version_end_of_support",
    "version_end_of_contract",
    "dependency_category",
    "dependency_name",
    "dependency_version",
    "dependency_end_of_support",
]


class CSVImportService:
    def __init__(self, db: Session):
        self.db = db

    def generate_template(self) -> bytes:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=CSV_HEADERS)
        writer.writeheader()
        return output.getvalue().encode("utf-8")

    def parse_date(self, value: str | None):
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Date invalide: {value}")

    def import_csv(self, file: UploadFile) -> dict[str, int]:
        content = file.file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        missing_headers = [header for header in CSV_HEADERS if header not in reader.fieldnames]
        if missing_headers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Colonnes manquantes: {', '.join(missing_headers)}",
            )

        created_projects = 0
        created_applications = 0
        created_versions = 0
        created_dependencies = 0

        for row in reader:
            project_name = row["project_name"].strip()
            if not project_name:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nom de projet manquant")
            project = self.db.query(Project).filter(Project.name == project_name).one_or_none()
            if not project:
                project = Project(name=project_name, team=row["project_team"], contact=row["project_contact"])
                self.db.add(project)
                self.db.flush()
                created_projects += 1

            application_name = row["application_name"].strip()
            if not application_name:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nom d'application manquant")
            application = (
                self.db.query(Application)
                .filter(Application.name == application_name, Application.project_id == project.id)
                .one_or_none()
            )
            if not application:
                application = Application(
                    name=application_name,
                    project_id=project.id,
                    description=row["application_description"],
                    owner=row["application_owner"],
                    criticity=row["application_criticity"] or None,
                    status=row["application_status"] or None,
                )
                self.db.add(application)
                self.db.flush()
                created_applications += 1

            if row.get("version_number"):
                existing_version = (
                    self.db.query(Version)
                    .filter(Version.application_id == application.id, Version.number == row["version_number"])
                    .one_or_none()
                )
                if not existing_version:
                    version = Version(
                        application_id=application.id,
                        number=row["version_number"],
                        end_of_support=self.parse_date(row["version_end_of_support"]),
                        end_of_contract=self.parse_date(row["version_end_of_contract"]),
                    )
                    self.db.add(version)
                    self.db.flush()
                    created_versions += 1

            if row.get("dependency_name"):
                category_value = row.get("dependency_category") or DependencyCategory.other.value
                try:
                    category = DependencyCategory(category_value)
                except ValueError:
                    category = DependencyCategory.other
                existing_dependency = (
                    self.db.query(Dependency)
                    .filter(
                        Dependency.application_id == application.id,
                        Dependency.name == row["dependency_name"],
                        Dependency.version == row.get("dependency_version"),
                    )
                    .one_or_none()
                )
                if not existing_dependency:
                    dependency = Dependency(
                        application_id=application.id,
                        category=category,
                        name=row["dependency_name"],
                        version=row.get("dependency_version"),
                        end_of_support=self.parse_date(row.get("dependency_end_of_support")),
                    )
                    self.db.add(dependency)
                    self.db.flush()
                    created_dependencies += 1

        self.db.commit()
        return {
            "projects_created": created_projects,
            "applications_created": created_applications,
            "versions_created": created_versions,
            "dependencies_created": created_dependencies,
        }
