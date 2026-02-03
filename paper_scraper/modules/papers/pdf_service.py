"""PDF upload and text extraction service."""

import asyncio
import io
import re
from datetime import timedelta
from uuid import UUID, uuid4

import fitz  # PyMuPDF
from minio import Minio

from paper_scraper.core.config import settings


class PDFService:
    """Service for PDF upload and text extraction."""

    def __init__(self):
        # Parse endpoint URL to get host
        endpoint = settings.S3_ENDPOINT.replace("http://", "").replace("https://", "")
        self.minio = Minio(
            endpoint,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY.get_secret_value(),
            secure=settings.S3_ENDPOINT.startswith("https"),
        )
        self.bucket = settings.S3_BUCKET_NAME
        self._bucket_initialized = False

    async def _ensure_bucket(self) -> None:
        """Ensure the bucket exists (async wrapper)."""
        if self._bucket_initialized:
            return

        exists = await asyncio.to_thread(self.minio.bucket_exists, self.bucket)
        if not exists:
            await asyncio.to_thread(self.minio.make_bucket, self.bucket)
        self._bucket_initialized = True

    async def upload_and_extract(
        self,
        file_content: bytes,
        filename: str,
        organization_id: UUID,
    ) -> dict:
        """
        Upload PDF to S3 and extract text/metadata.

        Args:
            file_content: PDF file bytes
            filename: Original filename
            organization_id: Organization UUID

        Returns:
            Dict with extracted metadata and S3 path
        """
        # Ensure bucket exists (lazy init)
        await self._ensure_bucket()

        # Generate unique path
        file_id = uuid4()
        s3_path = f"papers/{organization_id}/{file_id}/{filename}"

        # Upload to S3 (run in thread to avoid blocking)
        await asyncio.to_thread(
            self.minio.put_object,
            self.bucket,
            s3_path,
            io.BytesIO(file_content),
            len(file_content),
            "application/pdf",
        )

        # Extract text and metadata (CPU-bound, run in thread)
        extracted = await asyncio.to_thread(self._extract_from_pdf, file_content)
        extracted["pdf_path"] = s3_path

        return extracted

    def _extract_from_pdf(self, pdf_content: bytes) -> dict:
        """Extract text and metadata from PDF using PyMuPDF.

        Args:
            pdf_content: Raw PDF bytes.

        Returns:
            Dictionary with extracted title, abstract, authors, full_text, keywords, and source.
        """
        doc = fitz.open(stream=pdf_content, filetype="pdf")

        try:
            metadata = doc.metadata or {}
            title = metadata.get("title") or self._extract_title_from_text(doc)
            full_text = "\n".join(page.get_text("text") for page in doc)
            abstract = self._extract_abstract(full_text)
            authors = self._parse_authors(metadata.get("author", ""))

            return {
                "title": title or "Untitled PDF",
                "abstract": abstract,
                "authors": authors,
                "full_text": full_text[:100000],  # Limit to 100k chars
                "keywords": [],
                "source": "pdf",
            }
        finally:
            doc.close()

    def _parse_authors(self, author_string: str) -> list[dict]:
        """Parse comma-separated author names into author dictionaries.

        Args:
            author_string: Comma-separated author names.

        Returns:
            List of author dictionaries with name and affiliations.
        """
        if not author_string:
            return []
        return [
            {"name": name.strip(), "affiliations": []}
            for name in author_string.split(",")
            if name.strip()
        ]

    def _extract_title_from_text(self, doc: fitz.Document) -> str | None:
        """Extract title from first page (usually largest font text)."""
        if len(doc) == 0:
            return None

        page = doc[0]
        blocks = page.get_text("dict")["blocks"]

        # Find the largest text on first page (likely title)
        largest_size = 0
        title = None

        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["size"] > largest_size:
                            largest_size = span["size"]
                            title = span["text"]

        return title

    def _extract_abstract(self, text: str) -> str | None:
        """Extract abstract from full text."""
        # Try to find abstract section
        patterns = [
            r"(?i)abstract[:\s]*\n(.+?)(?=\n\n|\nintroduction|\n1\.)",
            r"(?i)abstract[:\s]*(.+?)(?=\n\n|keywords|introduction)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                abstract = match.group(1).strip()
                # Clean up
                abstract = " ".join(abstract.split())
                if len(abstract) > 100:  # Reasonable abstract length
                    return abstract[:2000]  # Limit length

        return None

    async def get_pdf_url(self, s3_path: str, expires_hours: int = 1) -> str:
        """Get a presigned URL for PDF download.

        Args:
            s3_path: S3 object path.
            expires_hours: URL expiry time in hours.

        Returns:
            Presigned URL for download.
        """
        return await asyncio.to_thread(
            self.minio.presigned_get_object,
            self.bucket,
            s3_path,
            timedelta(hours=expires_hours),
        )
