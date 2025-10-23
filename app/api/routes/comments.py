from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.entities import Application, Comment, TimelineEvent, User, UserRole
from app.schemas.entities import Comment as CommentSchema
from app.schemas.entities import CommentCreate, CommentUpdate

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("/", response_model=list[CommentSchema])
async def list_comments(
    application_id: int,
    db: Session = Depends(get_db),
    __: None = Depends(get_current_user),
) -> list[Comment]:
    return (
        db.query(Comment)
        .filter(Comment.application_id == application_id)
        .order_by(Comment.created_at.desc())
        .all()
    )


@router.post("/", response_model=CommentSchema, status_code=status.HTTP_201_CREATED)
async def create_comment(
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Comment:
    if current_user.role not in {UserRole.contributor, UserRole.admin}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Droits insuffisants")
    application = db.get(Application, payload.application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application inconnue")
    comment_data = payload.dict(exclude={"author_id"})
    comment = Comment(**comment_data, author_id=current_user.id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    event = TimelineEvent(
        application_id=comment.application_id,
        entity_type="comment",
        entity_id=comment.id,
        event_type="create",
        description=f"Commentaire ajouté par {current_user.name}",
        performed_by_id=current_user.id,
    )
    db.add(event)
    db.commit()
    return comment


@router.put("/{comment_id}", response_model=CommentSchema)
async def update_comment(
    comment_id: int,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Comment:
    comment = db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commentaire introuvable")
    if current_user.role not in {UserRole.admin} and comment.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Droits insuffisants")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(comment, field, value)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    event = TimelineEvent(
        application_id=comment.application_id,
        entity_type="comment",
        entity_id=comment.id,
        event_type="update",
        description="Commentaire mis à jour",
        performed_by_id=current_user.id,
    )
    db.add(event)
    db.commit()
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    comment = db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commentaire introuvable")
    if current_user.role not in {UserRole.admin} and comment.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Droits insuffisants")
    application_id = comment.application_id
    db.delete(comment)
    db.commit()
    event = TimelineEvent(
        application_id=application_id,
        entity_type="comment",
        entity_id=comment_id,
        event_type="delete",
        description="Commentaire supprimé",
        performed_by_id=current_user.id,
    )
    db.add(event)
    db.commit()
