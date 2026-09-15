"""
Auth routes. /auth/register only for now — /auth/login and /auth/me
are Day 5 (they need JWT issuance/verification, not built yet).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.auth import EmailAlreadyRegisteredError, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),  # noqa: B008 — FastAPI's DI pattern
) -> UserRead:
    try:
        user = await register_user(db, payload.email, payload.password)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    return UserRead.model_validate(user)
