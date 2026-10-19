"""
Object storage abstraction (StorageProvider interface).

Per the architecture doc: "swapping to S3 later doesn't touch calling
code" — application code depends only on the StorageProvider interface
below, never on boto3 or MinIO-specific details directly. MinIO (the
pgsty/silo fork, see docker-compose.yml) is used for local dev because
it speaks the same S3 API as real AWS S3, so the same S3StorageProvider
class (using boto3, the real AWS SDK) works against both — only the
endpoint URL and credentials differ.
"""

import asyncio
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from io import BytesIO
from typing import BinaryIO, TypeVar

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings

T = TypeVar("T")


class StorageError(Exception):
    """The storage backend failed or is unreachable. Translated from
    boto3's exception types so callers (and the global exception
    handler, which turns this into a 503) never depend on boto3."""


class StorageObjectNotFoundError(Exception):
    pass


class StorageProvider(ABC):
    """Abstract interface — any real backend (MinIO now, S3 in
    production, something else later) implements this. Application
    code (services, routes) should only ever depend on this interface,
    never import boto3 or a specific backend directly."""

    @abstractmethod
    async def upload(self, key: str, content: bytes) -> None: ...

    @abstractmethod
    async def upload_fileobj(self, key: str, fileobj: BinaryIO) -> None:
        """Streams a file-like object to storage without loading it
        fully into memory (boto3 switches to multipart for big files)."""

    @abstractmethod
    async def download(self, key: str) -> bytes: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def exists(self, key: str) -> bool: ...


def _is_not_found(exc: ClientError) -> bool:
    return str(exc.response.get("Error", {}).get("Code")) in (
        "404",
        "NoSuchKey",
        "NotFound",
        "NoSuchBucket",
    )


class S3StorageProvider(StorageProvider):
    """Real implementation using boto3 (the actual AWS SDK) against
    any S3-compatible endpoint — MinIO locally, real AWS S3 in
    production, with zero code changes between the two.

    boto3 is synchronous (blocking). Every call is pushed onto a worker
    thread with asyncio.to_thread so a slow or large transfer never
    freezes the event loop — which matters now that uploads can be tens
    of megabytes (Day 7's note said to revisit this at Stage 3).
    """

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
    ) -> None:
        self._bucket = bucket_name
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            # path-style addressing (bucket in the URL path, not a
            # subdomain) is what MinIO expects by default.
            config=Config(
                s3={"addressing_style": "path"},
                # Explicit timeouts: boto3 defaults (60s connect, 5 retries)
                # would let a dead storage server hang a request for minutes.
                connect_timeout=5,
                read_timeout=60,
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Creates the bucket if it doesn't exist yet, so local setup is
        just "docker compose up". Only a genuine "not found" triggers
        creation — any other failure (bad credentials, unreachable
        server) is reported as a StorageError instead of being masked
        by a doomed create attempt."""
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError as exc:
            if not _is_not_found(exc):
                raise StorageError(f"Cannot access bucket: {exc}") from exc
            try:
                self._client.create_bucket(Bucket=self._bucket)
            except (BotoCoreError, ClientError) as create_exc:
                raise StorageError(
                    f"Cannot create bucket: {create_exc}"
                ) from create_exc
        except BotoCoreError as exc:
            raise StorageError(f"Cannot reach object storage: {exc}") from exc

    async def _run(self, func: Callable[[], T]) -> T:
        try:
            return await asyncio.to_thread(func)
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(f"Object storage operation failed: {exc}") from exc

    async def upload(self, key: str, content: bytes) -> None:
        await self._run(
            lambda: self._client.put_object(
                Bucket=self._bucket, Key=key, Body=BytesIO(content)
            )
        )

    async def upload_fileobj(self, key: str, fileobj: BinaryIO) -> None:
        await self._run(lambda: self._client.upload_fileobj(fileobj, self._bucket, key))

    async def download(self, key: str) -> bytes:
        def _get() -> bytes:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            return response["Body"].read()

        try:
            return await asyncio.to_thread(_get)
        except ClientError as exc:
            if _is_not_found(exc):
                raise StorageObjectNotFoundError(key) from exc
            raise StorageError(f"Object storage operation failed: {exc}") from exc
        except BotoCoreError as exc:
            raise StorageError(f"Object storage operation failed: {exc}") from exc

    async def delete(self, key: str) -> None:
        await self._run(
            lambda: self._client.delete_object(Bucket=self._bucket, Key=key)
        )

    async def exists(self, key: str) -> bool:
        try:
            await asyncio.to_thread(
                lambda: self._client.head_object(Bucket=self._bucket, Key=key)
            )
            return True
        except ClientError as exc:
            if _is_not_found(exc):
                return False
            raise StorageError(f"Object storage operation failed: {exc}") from exc
        except BotoCoreError as exc:
            raise StorageError(f"Object storage operation failed: {exc}") from exc


_provider_instance: StorageProvider | None = None
_provider_lock = threading.Lock()


def get_storage_provider() -> StorageProvider:
    """Factory and FastAPI dependency — the one place that decides which
    concrete StorageProvider to build. Cached as a singleton (matching
    app.db.session.engine) because constructing it makes a real network
    call. FastAPI runs sync dependencies in a thread pool, so two first
    requests can arrive together: the lock stops both building one."""
    global _provider_instance
    if _provider_instance is None:
        with _provider_lock:
            if _provider_instance is None:
                _provider_instance = S3StorageProvider(
                    endpoint_url=settings.storage_endpoint_url,
                    access_key=settings.minio_root_user,
                    secret_key=settings.minio_root_password,
                    bucket_name=settings.storage_bucket_name,
                )
    return _provider_instance
