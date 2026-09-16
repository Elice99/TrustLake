"""
Auth routes: register, login, me.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.security import create_access_token
from app.db.session import get_db
from app.models import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserRead
from app.services.auth import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    authenticate_user,
    register_user,
)

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


@router.post("/login", response_model=Token)
async def login(
    # OAuth2PasswordRequestForm's field is literally named "username"
    # (that's the OAuth2 spec's field name, not ours) — we treat its
    # value as the user's email. This form-based shape (not a plain
    # JSON body) is what lets Swagger UI's "Authorize" button work
    # out of the box at /docs, which matters for a project you'll be
    # testing by hand a lot.
    form_data: OAuth2PasswordRequestForm = Depends(),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Token:
    try:
        user = await authenticate_user(db, form_data.username, form_data.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
async def read_current_user(
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> UserRead:
    return UserRead.model_validate(current_user)
