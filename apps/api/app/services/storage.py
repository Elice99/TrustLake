"""
Object storage abstraction (StorageProvider interface).

Per the architecture doc: "swapping to S3 later doesn't touch calling
code" — application code depends only on the StorageProvider interface
below, never on boto3 or MinIO-specific details directly. MinIO is
used for local dev because it speaks the same S3 API as real AWS S3,
so the same S3Provider class (using boto3, the real AWS SDK) works
against both — only the endpoint URL and credentials differ.
"""

from abc import ABC, abstractmethod
from io import BytesIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings


class StorageProvider(ABC):
    """Abstract interface — any real backend (MinIO now, S3 in
    production, something else later) implements this. Application
    code (services, routes) should only ever depend on this interface,
    never import boto3 or a specific backend directly."""

    @abstractmethod
    async def upload(self, key: str, content: bytes) -> None: ...

    @abstractmethod
    async def download(self, key: str) -> bytes: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def exists(self, key: str) -> bool: ...


class StorageObjectNotFoundError(Exception):
    pass


class S3StorageProvider(StorageProvider):
    """Real implementation using boto3 (the actual AWS SDK) against
    any S3-compatible endpoint — MinIO locally, real AWS S3 in
    production, with zero code changes between the two; only the
    endpoint_url/credentials passed in differ.

    boto3's client is synchronous (blocking) — there is no official
    async AWS SDK for Python that's as mature. Rather than pull in an
    extra third-party async-S3 library (more dependency surface for
    a Stage 2 abstraction), the sync calls are kept intentionally
    thin and fast (single object read/write), which is an acceptable
    tradeoff here. If this becomes a real bottleneck once file sizes
    are large (Stage 3+), revisit with a proper async wrapper then —
    not a premature optimization now.
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
            # subdomain) is what MinIO expects by default — virtual-
            # hosted-style (bucket-as-subdomain) is real AWS S3's
            # default, but MinIO doesn't do automatic DNS routing for
            # arbitrary bucket subdomains the way AWS does.
            config=Config(s3={"addressing_style": "path"}),
        )
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Creates the bucket if it doesn't exist yet — safe to call
        every time the app starts; a real production S3 bucket would
        typically be created once via infrastructure tooling, but for
        local MinIO dev this keeps setup to "just run docker compose
        up", no manual bucket-creation step."""
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            self._client.create_bucket(Bucket=self._bucket)

    async def upload(self, key: str, content: bytes) -> None:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=BytesIO(content))

    async def download(self, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            return response["Body"].read()
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
                raise StorageObjectNotFoundError(key) from exc
            raise

    async def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    async def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError:
            return False


_provider_instance: StorageProvider | None = None


def get_storage_provider() -> StorageProvider:
    """Factory — the one place that decides which concrete
    StorageProvider to build. A FastAPI route/service takes this as a
    dependency and only ever sees the abstract interface.

    Cached as a singleton (matching app.db.session.engine's pattern) —
    constructing S3StorageProvider does a real network call
    (_ensure_bucket_exists), so this must not run on every request."""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = S3StorageProvider(
            endpoint_url=settings.storage_endpoint_url,
            access_key=settings.minio_root_user,
            secret_key=settings.minio_root_password,
            bucket_name=settings.storage_bucket_name,
        )
    return _provider_instance
