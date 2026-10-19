"""
Dataset ingestion service (Stage 3): upload -> validate -> profile ->
store -> record. No FastAPI imports; routes translate the exceptions
raised here into HTTP responses.

ORDER OF OPERATIONS (deliberate):
  1. cheap checks (name, extension, size)
  2. parse + profile the file in memory   <- rejects bad files before
                                             anything is stored anywhere
  3. upload the original to object storage
  4. write database rows + audit events (one transaction, committed by
     get_db when the request finishes)

Storage is written BEFORE the database. If step 4 fails we may leave an
orphaned object in storage, which is harmless (nothing references it).
The opposite order could leave a database row pointing at a file that
doesn't exist, which is a real integrity bug. On a failure in step 4 we
make a best-effort delete of the object.
"""

import asyncio
import hashlib
import logging
import os
import uuid
from typing import BinaryIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEvent, Dataset, DatasetVersion, Profile, User
from app.schemas.profile import DatasetProfile
from app.services.profiling import profile_csv
from app.services.storage import StorageProvider

logger = logging.getLogger("trustlake.api")

# The client-supplied Content-Type is advisory only (browsers and
# Windows/Excel send several different values for CSV, and a client can
# claim anything). The real validation is that the file actually parses
# as CSV — this list only rejects obviously wrong declarations.
ALLOWED_CONTENT_TYPES = frozenset(
    {
        "text/csv",
        "application/csv",
        "application/vnd.ms-excel",
        "text/plain",
        "application/octet-stream",
    }
)
MAX_NAME_LENGTH = 255
_HASH_CHUNK_BYTES = 1024 * 1024


class InvalidUploadError(Exception):
    """Wrong file type (extension or declared content type)."""


class InvalidDatasetNameError(Exception):
    pass


class FileTooLargeError(Exception):
    pass


class DatasetNotFoundError(Exception):
    pass


def validate_upload_metadata(filename: str | None, content_type: str | None) -> str:
    """Returns the cleaned file name, or raises InvalidUploadError."""
    if not filename:
        raise InvalidUploadError("The upload has no file name.")
    # Some browsers send a full Windows path; keep only the last part.
    clean = os.path.basename(filename.replace("\\", "/")).strip()
    if not clean.lower().endswith(".csv"):
        raise InvalidUploadError("Only .csv files are supported.")
    if content_type:
        declared = content_type.split(";")[0].strip().lower()
        if declared not in ALLOWED_CONTENT_TYPES:
            raise InvalidUploadError(
                f"Unsupported content type '{declared}'. Upload a .csv file."
            )
    return clean


def _resolve_name(name: str | None, clean_filename: str) -> str:
    chosen = name.strip() if name and name.strip() else clean_filename[:-4].strip()
    if not chosen:
        raise InvalidDatasetNameError("The dataset name cannot be empty.")
    if len(chosen) > MAX_NAME_LENGTH:
        raise InvalidDatasetNameError(
            f"The dataset name is too long (maximum {MAX_NAME_LENGTH} characters)."
        )
    return chosen


def _file_size(fileobj: BinaryIO) -> int:
    fileobj.seek(0, os.SEEK_END)
    size = fileobj.tell()
    fileobj.seek(0)
    return size


def _hash_and_profile(fileobj: BinaryIO) -> tuple[str, DatasetProfile]:
    """CPU-bound (hashing + pandas), so the caller runs this on a worker
    thread to keep the event loop free for other requests."""
    digest = hashlib.sha256()
    fileobj.seek(0)
    while chunk := fileobj.read(_HASH_CHUNK_BYTES):
        digest.update(chunk)
    return digest.hexdigest(), profile_csv(fileobj)


async def _discard_stored_object(storage: StorageProvider, key: str) -> None:
    try:
        await storage.delete(key)
    except Exception:
        logger.warning("Could not remove orphaned object %s", key, exc_info=True)


async def ingest_csv_upload(
    session: AsyncSession,
    storage: StorageProvider,
    owner: User,
    *,
    filename: str | None,
    content_type: str | None,
    fileobj: BinaryIO,
    name: str | None,
    max_bytes: int,
) -> tuple[Dataset, DatasetVersion, DatasetProfile]:
    clean_filename = validate_upload_metadata(filename, content_type)
    dataset_name = _resolve_name(name, clean_filename)

    # Authoritative server-side size check, measured on the real bytes
    # received (a client-declared Content-Length can be missing or lie).
    size = _file_size(fileobj)
    if size > max_bytes:
        raise FileTooLargeError(
            f"The file is {size / (1024 * 1024):.1f} MB; the maximum allowed "
            f"size is {max_bytes / (1024 * 1024):.0f} MB."
        )

    # Raises CsvParseError for anything that isn't a usable CSV.
    sha256, profile = await asyncio.to_thread(_hash_and_profile, fileobj)

    dataset_id = uuid.uuid4()
    version_id = uuid.uuid4()
    # The key is built only from generated IDs, never from user input.
    storage_key = f"datasets/{dataset_id}/versions/{version_id}/original.csv"

    fileobj.seek(0)
    await storage.upload_fileobj(storage_key, fileobj)

    try:
        dataset = Dataset(id=dataset_id, name=dataset_name, owner_id=owner.id)
        session.add(dataset)
        await session.flush()  # the version row has a foreign key to this

        version = DatasetVersion(
            id=version_id,
            dataset_id=dataset_id,
            version_number=1,
            parent_version_id=None,
            storage_key=storage_key,
            size_bytes=size,
            content_sha256=sha256,
        )
        session.add(version)
        await session.flush()

        session.add(
            Profile(
                dataset_version_id=version_id,
                profiler_version=profile.profiler_version,
                profile=profile.model_dump(mode="json"),
            )
        )
        session.add(
            AuditEvent(
                actor_id=owner.id,
                action="dataset_uploaded",
                entity_type="dataset",
                entity_id=dataset_id,
                event_metadata={
                    "filename": clean_filename,
                    "size_bytes": size,
                    "content_sha256": sha256,
                    "version_number": 1,
                },
            )
        )
        session.add(
            AuditEvent(
                actor_id=owner.id,
                action="dataset_profiled",
                entity_type="dataset_version",
                entity_id=version_id,
                event_metadata={
                    "dataset_id": str(dataset_id),
                    "row_count": profile.summary.row_count,
                    "column_count": profile.summary.column_count,
                    "profiler_version": profile.profiler_version,
                },
            )
        )
        await session.flush()
    except Exception:
        await _discard_stored_object(storage, storage_key)
        raise

    return dataset, version, profile


async def list_datasets(session: AsyncSession, owner_id: uuid.UUID) -> list[Dataset]:
    result = await session.execute(
        select(Dataset)
        .where(Dataset.owner_id == owner_id)
        .order_by(Dataset.created_at.desc())
    )
    return list(result.scalars())


async def get_dataset_detail(
    session: AsyncSession, owner_id: uuid.UUID, dataset_id: uuid.UUID
) -> tuple[Dataset, DatasetVersion, DatasetProfile]:
    """Owner-scoped at the query level (architecture doc section 8): a
    dataset that exists but belongs to someone else is indistinguishable
    from one that doesn't exist, so ids can't be probed."""
    dataset = (
        await session.execute(
            select(Dataset).where(
                Dataset.id == dataset_id, Dataset.owner_id == owner_id
            )
        )
    ).scalar_one_or_none()
    if dataset is None:
        raise DatasetNotFoundError(str(dataset_id))

    version = (
        await session.execute(
            select(DatasetVersion)
            .where(DatasetVersion.dataset_id == dataset_id)
            .order_by(DatasetVersion.version_number.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    profile_row = (
        (
            await session.execute(
                select(Profile).where(Profile.dataset_version_id == version.id)
            )
        ).scalar_one_or_none()
        if version
        else None
    )
    if version is None or profile_row is None:
        # Ingestion writes dataset + version + profile together, so this
        # means the data is inconsistent. Fail loudly rather than guess.
        raise RuntimeError(f"Dataset {dataset_id} is missing its version or profile")

    return dataset, version, DatasetProfile.model_validate(profile_row.profile)
