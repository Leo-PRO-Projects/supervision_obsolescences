from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models.entities import ActionPlan, TimelineEvent, UserRole
from app.schemas.entities import ActionPlan as ActionPlanSchema
from app.schemas.entities import ActionPlanCreate, ActionPlanUpdate

router = APIRouter(prefix="/action-plans", tags=["action_plans"])


@router.get("/", response_model=List[ActionPlanSchema])
async def list_action_plans(
    application_id: int | None = None,
    db: Session = Depends(get_db),
    __: None = Depends(get_current_user),
) -> List[ActionPlan]:
    query = db.query(ActionPlan)
    if application_id:
        query = query.filter(ActionPlan.application_id == application_id)
    return query.order_by(ActionPlan.due_date).all()


@router.post("/", response_model=ActionPlanSchema, status_code=status.HTTP_201_CREATED)
async def create_action_plan(
    payload: ActionPlanCreate,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> ActionPlan:
    action_plan = ActionPlan(**payload.dict())
    db.add(action_plan)
    db.commit()
    db.refresh(action_plan)
    event = TimelineEvent(
        application_id=action_plan.application_id,
        entity_type="action_plan",
        entity_id=action_plan.id,
        event_type="create",
        description=f"Plan d'action '{action_plan.title}' créé",
    )
    db.add(event)
    db.commit()
    return action_plan


@router.put("/{action_plan_id}", response_model=ActionPlanSchema)
async def update_action_plan(
    action_plan_id: int,
    payload: ActionPlanUpdate,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> ActionPlan:
    action_plan = db.get(ActionPlan, action_plan_id)
    if not action_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan d'action introuvable")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(action_plan, field, value)
    db.add(action_plan)
    db.commit()
    db.refresh(action_plan)
    event = TimelineEvent(
        application_id=action_plan.application_id,
        entity_type="action_plan",
        entity_id=action_plan.id,
        event_type="update",
        description=f"Plan d'action '{action_plan.title}' mis à jour",
    )
    db.add(event)
    db.commit()
    return action_plan


# NOTE:
# FastAPI enforces that a route returning a 204 status code does not emit any
# response body. Returning ``None`` (the default implicit return value) would
# still instruct FastAPI to serialize ``null`` in the body, which raises an
# assertion during application startup. Declaring ``response_class=Response``
# returning an explicit empty ``Response`` avoids the problem, and annotating
# the endpoint accordingly prevents FastAPI from assuming a response model for
# status code 204.
@router.delete(
    "/{action_plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_action_plan(
    action_plan_id: int,
    db: Session = Depends(get_db),
    __: None = Depends(require_role(UserRole.contributor)),
) -> Response:
    action_plan = db.get(ActionPlan, action_plan_id)
    if not action_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan d'action introuvable")
    title = action_plan.title
    application_id = action_plan.application_id
    db.delete(action_plan)
    db.commit()
    event = TimelineEvent(
        application_id=application_id,
        entity_type="action_plan",
        entity_id=action_plan_id,
        event_type="delete",
        description=f"Plan d'action '{title}' supprimé",
    )
    db.add(event)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
