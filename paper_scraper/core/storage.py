"""S3-compatible file storage service (MinIO).

Provides upload, download URL generation, and deletion
for files stored in MinIO/S3-compatible object storage.
"""

import logging
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError

from paper_scraper.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for file upload/download to S3-compatible storage."""

    def __init__(
        self,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        bucket: str | None = None,
        region: str | None = None,
    ):
        """Initialize the storage service.

        Args:
            endpoint_url: S3 endpoint URL. Defaults to settings.S3_ENDPOINT.
            access_key: AWS access key. Defaults to settings.S3_ACCESS_KEY.
            secret_key: AWS secret key. Defaults to settings.S3_SECRET_KEY.
            bucket: S3 bucket name. Defaults to settings.S3_BUCKET_NAME.
            region: AWS region. Defaults to settings.S3_REGION.
        """
        self.endpoint_url = endpoint_url or settings.S3_ENDPOINT
        self.bucket = bucket or settings.S3_BUCKET_NAME
        self._client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=access_key or settings.S3_ACCESS_KEY,
            aws_secret_access_key=(secret_key or settings.S3_SECRET_KEY.get_secret_value()),
            region_name=region or settings.S3_REGION,
        )

    def ensure_bucket(self) -> None:
        """Ensure the storage bucket exists, creating it if necessary."""
        try:
            self._client.head_bucket(Bucket=self.bucket)
        except ClientError:
            logger.info("Creating bucket: %s", self.bucket)
            self._client.create_bucket(Bucket=self.bucket)

    @staticmethod
    def _validate_key(key: str) -> None:
        """Validate storage key to prevent path traversal.

        Args:
            key: S3 object key to validate.

        Raises:
            ValueError: If the key contains path traversal sequences.
        """
        if ".." in key or key.startswith("/") or "\x00" in key:
            raise ValueError(f"Invalid storage key: {key!r}")

    def upload_file(
        self,
        file_content: bytes,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload file and return the storage key.

        Args:
            file_content: Raw file bytes to upload.
            key: S3 object key (path within bucket).
            content_type: MIME type of the file.

        Returns:
            The storage key for the uploaded file.

        Raises:
            ClientError: If the upload fails.
            ValueError: If the key is invalid.
        """
        self._validate_key(key)
        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=file_content,
            ContentType=content_type,
        )
        return key

    def get_download_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a pre-signed download URL.

        Args:
            key: S3 object key.
            expires_in: URL expiry time in seconds (default 1 hour, max 24 hours).

        Returns:
            Pre-signed URL string.
        """
        self._validate_key(key)
        expires_in = min(expires_in, 86400)  # Cap at 24 hours
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def download_file(self, key: str) -> bytes:
        """Download a file from storage and return raw bytes.

        Args:
            key: S3 object key.

        Returns:
            Raw file content.
        """
        self._validate_key(key)
        response = self._client.get_object(Bucket=self.bucket, Key=key)
        try:
            return response["Body"].read()
        finally:
            response["Body"].close()

    def delete_file(self, key: str) -> None:
        """Delete a file from storage.

        Args:
            key: S3 object key to delete.
        """
        self._validate_key(key)
        self._client.delete_object(Bucket=self.bucket, Key=key)

    def file_exists(self, key: str) -> bool:
        """Check if a file exists in storage.

        Args:
            key: S3 object key.

        Returns:
            True if the file exists, False otherwise.
        """
        self._validate_key(key)
        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False


@lru_cache
def get_storage_service() -> StorageService:
    """Get cached StorageService instance."""
    return StorageService()
