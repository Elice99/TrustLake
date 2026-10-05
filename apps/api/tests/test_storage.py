"""
StorageProvider tests, using moto (an in-process mock of the real AWS
S3 API) rather than a live MinIO/S3 server — moto intercepts the exact
same boto3 calls S3StorageProvider makes, so this genuinely exercises
the real code path (bucket creation, put/get/delete/head), just
without needing network access to a real object store. The actual
MinIO container (docker-compose.yml) is what proves this works
end-to-end against the real thing.
"""

import pytest
from moto import mock_aws

from app.services.storage import S3StorageProvider, StorageObjectNotFoundError


@pytest.fixture
def provider():  # type: ignore[no-untyped-def]
    with mock_aws():
        yield S3StorageProvider(
            endpoint_url="https://s3.amazonaws.com",
            access_key="test-access-key",
            secret_key="test-secret-key",
            bucket_name="trustlake-test-bucket",
        )


async def test_upload_then_download_roundtrips_exact_bytes(provider) -> None:  # type: ignore[no-untyped-def]
    await provider.upload("some/key.csv", b"col1,col2\n1,2\n")
    result = await provider.download("some/key.csv")
    assert result == b"col1,col2\n1,2\n"


async def test_exists_reflects_real_state(provider) -> None:  # type: ignore[no-untyped-def]
    assert await provider.exists("missing-key.txt") is False
    await provider.upload("present-key.txt", b"data")
    assert await provider.exists("present-key.txt") is True


async def test_download_missing_key_raises_clear_error(provider) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(StorageObjectNotFoundError):
        await provider.download("does-not-exist.txt")


async def test_delete_actually_removes_the_object(provider) -> None:  # type: ignore[no-untyped-def]
    await provider.upload("to-delete.txt", b"data")
    assert await provider.exists("to-delete.txt") is True

    await provider.delete("to-delete.txt")
    assert await provider.exists("to-delete.txt") is False


async def test_bucket_is_auto_created_on_first_use() -> None:
    """A fresh mocked S3 account with no buckets at all — confirms
    _ensure_bucket_exists really does create it, not just assume it's
    already there (which is exactly what happens on a brand new MinIO
    container with an empty data volume)."""
    with mock_aws():
        provider = S3StorageProvider(
            endpoint_url="https://s3.amazonaws.com",
            access_key="test-access-key",
            secret_key="test-secret-key",
            bucket_name="a-bucket-that-does-not-exist-yet",
        )
        await provider.upload("proof.txt", b"it worked")
        assert await provider.download("proof.txt") == b"it worked"
