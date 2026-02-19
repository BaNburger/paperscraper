"""Full-text hydration and chunking utilities for library reader."""

from __future__ import annotations

import asyncio
import html
import ipaddress
import logging
import re
import socket
from dataclasses import dataclass
from urllib.parse import quote, urljoin, urlparse

import httpx

from paper_scraper.core.config import settings
from paper_scraper.core.storage import get_storage_service

logger = logging.getLogger(__name__)


@dataclass
class HydratedText:
    """Hydrated full-text content and source metadata."""

    text: str
    source: str


@dataclass
class TextChunk:
    """Chunked text record."""

    chunk_index: int
    page_number: int | None
    text: str
    char_start: int
    char_end: int


class LibraryTextService:
    """Service for extracting and hydrating full text."""

    def __init__(self) -> None:
        self._storage = get_storage_service()

    def chunk_text(
        self,
        text: str,
        *,
        chunk_size: int = 1200,
        overlap: int = 180,
    ) -> list[TextChunk]:
        """Split full text into deterministic overlapping chunks."""
        cleaned = re.sub(r"\s+", " ", text).strip()
        if not cleaned:
            return []

        chunks: list[TextChunk] = []
        idx = 0
        chunk_index = 0
        length = len(cleaned)

        while idx < length:
            end = min(idx + chunk_size, length)
            # Prefer ending at punctuation when possible for readability.
            if end < length:
                window = cleaned[idx:end]
                split_positions = [window.rfind(c) for c in [". ", "! ", "? ", "; ", ": "]]
                split_pos = max(split_positions)
                if split_pos > chunk_size // 2:
                    end = idx + split_pos + 1

            chunk_text = cleaned[idx:end].strip()
            if chunk_text:
                chunks.append(
                    TextChunk(
                        chunk_index=chunk_index,
                        page_number=None,
                        text=chunk_text,
                        char_start=idx,
                        char_end=end,
                    )
                )
                chunk_index += 1

            if end >= length:
                break
            idx = max(end - overlap, idx + 1)

        return chunks

    def extract_text_from_pdf_bytes(self, data: bytes) -> str:
        """Extract text from PDF bytes using PyMuPDF."""
        try:
            import fitz  # Lazy import

            doc = fitz.open(stream=data, filetype="pdf")
            try:
                return "\n".join(page.get_text("text") for page in doc).strip()
            finally:
                doc.close()
        except Exception as exc:
            logger.warning("PDF extraction failed: %s", exc)
            return ""

    async def hydrate_from_pdf_path(self, pdf_path: str) -> HydratedText | None:
        """Hydrate full text from stored PDF path."""
        try:
            pdf_bytes = self._storage.download_file(pdf_path)
        except Exception as exc:
            logger.warning("Failed to download stored PDF %s: %s", pdf_path, exc)
            return None

        extracted = self.extract_text_from_pdf_bytes(pdf_bytes)
        if not extracted:
            return None
        return HydratedText(text=extracted, source="stored_pdf")

    async def hydrate_from_oa_sources(self, doi: str) -> HydratedText | None:
        """Hydrate full text from OA sources in preferred order."""
        normalized_doi = doi.strip().lower()
        if normalized_doi.startswith("https://doi.org/"):
            normalized_doi = normalized_doi.replace("https://doi.org/", "", 1)
        if normalized_doi.startswith("http://dx.doi.org/"):
            normalized_doi = normalized_doi.replace("http://dx.doi.org/", "", 1)

        candidates = await self._resolve_oa_urls(normalized_doi)
        for candidate in candidates:
            text = await self._fetch_candidate_text(candidate)
            if text:
                return HydratedText(text=text, source=candidate["source"])

        return None

    async def _resolve_oa_urls(self, doi: str) -> list[dict[str, str]]:
        """Resolve OA candidates from OpenAlex, Crossref, and Semantic Scholar."""
        candidates: list[dict[str, str]] = []

        # 1) OpenAlex
        openalex_url = (
            f"{settings.OPENALEX_BASE_URL}/works/{quote('https://doi.org/' + doi, safe='')}"
        )
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    openalex_url, params={"mailto": settings.OPENALEX_EMAIL}
                )
                if response.status_code == 200:
                    data = response.json()
                    best_oa = data.get("best_oa_location") or {}
                    pdf_url = best_oa.get("pdf_url")
                    landing_url = best_oa.get("landing_page_url")
                    if isinstance(pdf_url, str):
                        candidates.append({"source": "openalex_pdf", "url": pdf_url, "type": "pdf"})
                    if isinstance(landing_url, str):
                        candidates.append(
                            {"source": "openalex_landing", "url": landing_url, "type": "html"}
                        )
        except Exception as exc:
            logger.debug("OpenAlex OA resolve failed for DOI %s: %s", doi, exc)

        # 2) Crossref
        crossref_url = f"{settings.CROSSREF_BASE_URL}/works/{quote(doi, safe='')}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    crossref_url,
                    headers={"User-Agent": f"PaperScraper/2.0 (mailto:{settings.CROSSREF_EMAIL})"},
                )
                if response.status_code == 200:
                    message = response.json().get("message", {})
                    for link in message.get("link", []) or []:
                        if not isinstance(link, dict):
                            continue
                        url = link.get("URL")
                        content_type = (link.get("content-type") or "").lower()
                        if isinstance(url, str):
                            if "pdf" in content_type or url.lower().endswith(".pdf"):
                                candidates.append(
                                    {"source": "crossref_pdf", "url": url, "type": "pdf"}
                                )
                            else:
                                candidates.append(
                                    {"source": "crossref_link", "url": url, "type": "html"}
                                )
        except Exception as exc:
            logger.debug("Crossref OA resolve failed for DOI %s: %s", doi, exc)

        # 3) Semantic Scholar
        semsch_url = f"{settings.SEMANTIC_SCHOLAR_BASE_URL}/paper/DOI:{quote(doi, safe='')}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {}
                if settings.SEMANTIC_SCHOLAR_API_KEY:
                    headers["x-api-key"] = settings.SEMANTIC_SCHOLAR_API_KEY
                response = await client.get(
                    semsch_url,
                    params={"fields": "openAccessPdf,url"},
                    headers=headers,
                )
                if response.status_code == 200:
                    data = response.json()
                    oa_pdf = (data.get("openAccessPdf") or {}).get("url")
                    if isinstance(oa_pdf, str):
                        candidates.append(
                            {"source": "semantic_scholar_pdf", "url": oa_pdf, "type": "pdf"}
                        )
                    paper_url = data.get("url")
                    if isinstance(paper_url, str):
                        candidates.append(
                            {"source": "semantic_scholar_link", "url": paper_url, "type": "html"}
                        )
        except Exception as exc:
            logger.debug("Semantic Scholar OA resolve failed for DOI %s: %s", doi, exc)

        # Preserve order, de-duplicate URLs.
        seen: set[str] = set()
        unique: list[dict[str, str]] = []
        for item in candidates:
            url = item.get("url", "")
            if url and url not in seen:
                unique.append(item)
                seen.add(url)
        return unique

    async def _fetch_candidate_text(self, candidate: dict[str, str]) -> str:
        """Fetch and parse text from an OA candidate URL."""
        url = candidate.get("url")
        if not url:
            return ""

        if not await self._is_safe_url(url):
            logger.debug("Blocked unsafe OA candidate URL: %s", url)
            return ""

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
                current_url = url
                response: httpx.Response | None = None
                for _ in range(5):
                    response = await client.get(current_url)
                    if response.status_code not in {301, 302, 303, 307, 308}:
                        break

                    location = response.headers.get("Location")
                    if not location:
                        break
                    redirected_url = urljoin(current_url, location)
                    if not await self._is_safe_url(redirected_url):
                        logger.debug("Blocked unsafe OA redirect URL: %s", redirected_url)
                        return ""
                    current_url = redirected_url

                if response is None:
                    return ""
                response.raise_for_status()
        except Exception as exc:
            logger.debug("Failed to fetch OA candidate %s: %s", url, exc)
            return ""

        content_type = (response.headers.get("content-type") or "").lower()
        candidate_type = candidate.get("type")
        is_pdf = "pdf" in content_type or candidate_type == "pdf" or url.lower().endswith(".pdf")

        if is_pdf:
            return self.extract_text_from_pdf_bytes(response.content)

        try:
            html_text = response.text
        except UnicodeDecodeError:
            html_text = response.content.decode("utf-8", errors="ignore")

        # Minimal HTML-to-text cleanup without extra dependencies.
        html_text = re.sub(r"(?is)<script.*?>.*?</script>", " ", html_text)
        html_text = re.sub(r"(?is)<style.*?>.*?</style>", " ", html_text)
        html_text = re.sub(r"(?is)<[^>]+>", " ", html_text)
        html_text = html.unescape(html_text)
        html_text = re.sub(r"\s+", " ", html_text).strip()

        if len(html_text) < 500:
            return ""
        return html_text

    async def _is_safe_url(self, url: str) -> bool:
        """Validate URL to mitigate SSRF to internal networks."""
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        if not parsed.hostname:
            return False

        hostname = parsed.hostname.strip().lower()
        if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
            return False

        try:
            ip_literal = ipaddress.ip_address(hostname)
            return not self._is_forbidden_ip(ip_literal)
        except ValueError:
            pass

        try:
            infos = await self._resolve_host_ips(hostname, parsed.port)
        except Exception:
            return False

        if not infos:
            return False
        return all(not self._is_forbidden_ip(ip) for ip in infos)

    async def _resolve_host_ips(
        self,
        hostname: str,
        port: int | None,
    ) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
        """Resolve host to IP addresses."""
        lookup_port = port or 443
        addrinfo = await asyncio.to_thread(socket.getaddrinfo, hostname, lookup_port)
        ips: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
        for info in addrinfo:
            sockaddr = info[4]
            ip_str = sockaddr[0]
            try:
                ips.append(ipaddress.ip_address(ip_str))
            except ValueError:
                continue
        return ips

    @staticmethod
    def _is_forbidden_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        """Reject local/private/link-local/reserved network targets."""
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        )
