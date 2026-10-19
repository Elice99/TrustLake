"""
Dataset routes: upload (with automatic profiling), list, detail.
All routes require authentication and are scoped to the caller's own data.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models import User
from app.schemas.dataset import DatasetDetail, DatasetRead, DatasetVersionRead
from app.services.datasets import (
    DatasetNotFoundError,
    FileTooLargeError,
    InvalidDatasetNameError,
    InvalidUploadError,
    get_dataset_detail,
    ingest_csv_upload,
    list_datasets,
)
from app.services.profiling import CsvParseError
from app.services.storage import StorageProvider, get_storage_provider

router = APIRouter(prefix="/datasets", tags=["datasets"])

# 413 and 415 are written as numbers: the named constants have been
# renamed across Starlette/Python versions, the numbers never change.
HTTP_413 = 413  # file too large
HTTP_415 = 415  # unsupported file type


@router.post("", response_model=DatasetDetail, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: Annotated[UploadFile, File(description="A UTF-8, comma-separated .csv file")],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
    name: Annotated[str | None, Form()] = None,
) -> DatasetDetail:
    """Validates, profiles, and stores a CSV. The profile is computed
    now and saved, so viewing it later costs nothing."""
    try:
        dataset, version, profile = await ingest_csv_upload(
            db,
            storage,
            current_user,
            filename=file.filename,
            content_type=file.content_type,
            fileobj=file.file,
            name=name,
            max_bytes=settings.max_upload_size_mb * 1024 * 1024,
        )
    except InvalidUploadError as exc:
        raise HTTPException(status_code=HTTP_415, detail=str(exc)) from exc
    except FileTooLargeError as exc:
        raise HTTPException(status_code=HTTP_413, detail=str(exc)) from exc
    except (CsvParseError, InvalidDatasetNameError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return DatasetDetail(
        dataset=DatasetRead.model_validate(dataset),
        version=DatasetVersionRead.model_validate(version),
        profile=profile,
    )


@router.get("", response_model=list[DatasetRead])
async def list_my_datasets(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DatasetRead]:
    datasets = await list_datasets(db, current_user.id)
    return [DatasetRead.model_validate(d) for d in datasets]


@router.get("/{dataset_id}", response_model=DatasetDetail)
async def get_dataset(
    dataset_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DatasetDetail:
    try:
        dataset, version, profile = await get_dataset_detail(
            db, current_user.id, dataset_id
        )
    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        ) from exc

    return DatasetDetail(
        dataset=DatasetRead.model_validate(dataset),
        version=DatasetVersionRead.model_validate(version),
        profile=profile,
    )
