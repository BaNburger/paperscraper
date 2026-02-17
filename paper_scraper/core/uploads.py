"""Shared upload validation and storage key helpers."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

DEFAULT_CHUNK_SIZE = 64 * 1024


def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filename for safe storage key composition."""
    base = os.path.basename(filename).strip()
    if not base:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    return sanitized[:255]


def build_storage_key(scope: str, resource_id: str, filename: str) -> str:
    """Build deterministic scoped storage key with unique prefix."""
    safe_filename = sanitize_filename(filename)
    unique_prefix = uuid4().hex[:12]
    return f"{scope}/{resource_id}/{unique_prefix}_{safe_filename}"


def validate_content_type(
    content_type: str | None,
    allowed_mime_types: Mapping[str, bytes | None],
) -> str:
    """Validate upload content type against allow-list."""
    normalized = content_type or "application/octet-stream"
    if normalized not in allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {normalized}",
        )
    return normalized


def validate_magic_bytes(content: bytes, expected_magic: bytes | None) -> None:
    """Validate file signature when an expected magic sequence is provided."""
    if expected_magic is not None and not content.startswith(expected_magic):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match declared MIME type",
        )


async def read_upload_content(
    file: UploadFile,
    *,
    max_size: int,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> tuple[bytes, int]:
    """Read uploaded file in chunks and enforce max size."""
    chunks: list[bytes] = []
    total_size = 0

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large (max {max_size // 1_000_000}MB)",
            )
        chunks.append(chunk)

    return b"".join(chunks), total_size


def validate_pdf_structure(content: bytes) -> None:
    """Validate basic PDF header and EOF markers."""
    if len(content) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is too small to be a valid PDF",
        )
    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF file: missing PDF header signature",
        )
    last_chunk = content[-1024:] if len(content) > 1024 else content
    if b"%%EOF" not in last_chunk:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF file: missing EOF marker",
        )
