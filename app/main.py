from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    action_plans,
    applications,
    auth,
    catalog,
    comments,
    dashboard,
    dependencies,
    import_export,
    notifications,
    projects,
    settings,
    timeline,
    users,
    versions,
)
from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.logging_config import configure_logging
from app.tasks.scheduler import start_scheduler

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title=settings.app_name, openapi_url=f"{settings.api_v1_str}/openapi.json")

if settings.backend_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router, prefix=settings.api_v1_str)
app.include_router(projects.router, prefix=settings.api_v1_str)
app.include_router(applications.router, prefix=settings.api_v1_str)
app.include_router(versions.router, prefix=settings.api_v1_str)
app.include_router(dependencies.router, prefix=settings.api_v1_str)
app.include_router(comments.router, prefix=settings.api_v1_str)
app.include_router(action_plans.router, prefix=settings.api_v1_str)
app.include_router(timeline.router, prefix=settings.api_v1_str)
app.include_router(notifications.router, prefix=settings.api_v1_str)
app.include_router(dashboard.router, prefix=settings.api_v1_str)
app.include_router(import_export.router, prefix=settings.api_v1_str)
app.include_router(catalog.router, prefix=settings.api_v1_str)
app.include_router(settings.router, prefix=settings.api_v1_str)
app.include_router(users.router, prefix=settings.api_v1_str)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

start_scheduler(app)


@app.on_event("startup")
async def on_startup() -> None:  # pragma: no cover - initialization
    Base.metadata.create_all(bind=engine)
    logger.info("Application démarrée")


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    index_path = "frontend/templates/index.html"
    with open(index_path, "r", encoding="utf-8") as file:
        return HTMLResponse(file.read())
