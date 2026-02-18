from __future__ import annotations

import re
from pathlib import Path

from .common import Finding, iter_files, iter_router_routes, to_posix_rel

FORBIDDEN_SOURCE_ROUTE_TOKENS = (
    "/sources/",
    "openalex",
    "pubmed",
    "arxiv",
    "semantic-scholar",
    "semantic_scholar",
)

SOURCE_RUN_ROUTE_RE = re.compile(r"/sources/.*/runs")
PRIVATE_METHOD_CALL_RE = re.compile(r"\._[A-Za-z][A-Za-z0-9_]*\s*\(")
PLAIN_SECRET_RE = re.compile(r"plain:")

STORAGE_PATTERNS = (
    re.compile(r"\bimport\s+boto3\b"),
    re.compile(r"\bfrom\s+minio\s+import\b"),
    re.compile(r"\bMinio\s*\("),
    re.compile(r"\bboto3\.client\s*\("),
    re.compile(r"\.put_object\s*\("),
)


def _line_number(text: str, match: re.Match[str]) -> int:
    return text.count("\n", 0, match.start()) + 1


def lint(repo: Path) -> list[Finding]:
    findings: list[Finding] = []

    papers_router = repo / "paper_scraper/modules/papers/router.py"
    ingestion_router = repo / "paper_scraper/modules/ingestion/router.py"

    if papers_router.exists():
        text = papers_router.read_text(encoding="utf-8")
        rel_path = to_posix_rel(papers_router, repo)
        for route, line in iter_router_routes(text):
            if any(token in route for token in FORBIDDEN_SOURCE_ROUTE_TOKENS):
                findings.append(
                    Finding(
                        rule_id="PSA001",
                        path=rel_path,
                        line=line,
                        message=(
                            f"Source ingestion route '{route}' is forbidden in papers router. "
                            "Use ingestion router only."
                        ),
                    )
                )

    modules_root = repo / "paper_scraper/modules"
    if modules_root.exists():
        for router_file in modules_root.rglob("router.py"):
            rel_path = to_posix_rel(router_file, repo)
            text = router_file.read_text(encoding="utf-8")

            if router_file != ingestion_router:
                for route, line in iter_router_routes(text):
                    if SOURCE_RUN_ROUTE_RE.search(route):
                        findings.append(
                            Finding(
                                rule_id="PSA002",
                                path=rel_path,
                                line=line,
                                message=(
                                    f"Source run route '{route}' is only allowed in ingestion router."
                                ),
                            )
                        )

            for match in PRIVATE_METHOD_CALL_RE.finditer(text):
                findings.append(
                    Finding(
                        rule_id="PSA004",
                        path=rel_path,
                        line=_line_number(text, match),
                        message="Router calls private service method. Use public service APIs only.",
                    )
                )

    storage_file = repo / "paper_scraper/core/storage.py"
    py_root = repo / "paper_scraper"
    if py_root.exists():
        for py_file in iter_files(py_root, suffixes=(".py",)):
            if py_file == storage_file:
                continue
            rel_path = to_posix_rel(py_file, repo)
            text = py_file.read_text(encoding="utf-8")

            for pattern in STORAGE_PATTERNS:
                for match in pattern.finditer(text):
                    findings.append(
                        Finding(
                            rule_id="PSA003",
                            path=rel_path,
                            line=_line_number(text, match),
                            message=(
                                "Direct storage SDK usage is forbidden outside "
                                "paper_scraper/core/storage.py."
                            ),
                        )
                    )

            for match in PLAIN_SECRET_RE.finditer(text):
                findings.append(
                    Finding(
                        rule_id="PSA005",
                        path=rel_path,
                        line=_line_number(text, match),
                        message="Legacy secret format 'plain:' is forbidden.",
                    )
                )

    for secret_file in (
        repo / "paper_scraper/modules/model_settings/service.py",
        repo / "paper_scraper/modules/scoring/service.py",
    ):
        if not secret_file.exists():
            continue
        text = secret_file.read_text(encoding="utf-8")
        if "enc:v1:" not in text:
            findings.append(
                Finding(
                    rule_id="PSA005",
                    path=to_posix_rel(secret_file, repo),
                    line=1,
                    message="Encrypted secret marker 'enc:v1:' is required in secret handling.",
                )
            )

    return findings

