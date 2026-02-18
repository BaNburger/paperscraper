from __future__ import annotations

import re
from pathlib import Path

from .common import Finding, iter_files, to_posix_rel

TS_SUFFIXES = (".ts", ".tsx")

API_LITERAL_RE = re.compile(r"""["']/api/v1/""")
FETCH_RE = re.compile(r"\bfetch\s*\(")
AXIOS_IMPORT_RE = re.compile(r"""(?:from|import)\s+['"]axios['"]|import\s+axios\b""")
AXIOS_DOT_RE = re.compile(r"\baxios\.")
DTO_IMPORT_RE = re.compile(r"""from\s+['"][^'"]*types(?:/index)?['"]""")
QUERY_KEY_LITERAL_RE = re.compile(r"queryKey\s*:\s*\[")
RESEARCH_GROUP_RE = re.compile(r"\bResearchGroup\b")
STORAGE_CALL_RE = re.compile(
    r"(?:localStorage|sessionStorage)\.(?:getItem|setItem|removeItem)\(\s*['\"]([^'\"]+)['\"]"
)
ROUTE_IMPORT_RE = re.compile(r"""from\s+['"][^'"]*config/routes['"]""")

INFRA_ROUTE_FILES = (
    "frontend/src/App.tsx",
    "frontend/src/components/CommandPalette.tsx",
    "frontend/src/hooks/useKeyboardShortcuts.ts",
    "frontend/src/lib/prefetch.ts",
    "frontend/src/components/layout/MobileMenu.tsx",
    "frontend/src/components/layout/Sidebar.tsx",
    "frontend/src/components/layout/MobileBottomNav.tsx",
)

HARDCODED_ROUTE_PATTERNS = (
    re.compile(r"""navigate\(\s*['"](/[^'"]+)['"]"""),
    re.compile(r"""\bto\s*=\s*['"](/[^'"]+)['"]"""),
    re.compile(r"""\bhref\s*=\s*['"](/[^'"]+)['"]"""),
    re.compile(r"""\bpath\s*:\s*['"](/[^'"]+)['"]"""),
)


def _line_number(text: str, match: re.Match[str]) -> int:
    return text.count("\n", 0, match.start()) + 1


def _is_test_file(path: str) -> bool:
    return path.endswith(".test.ts") or path.endswith(".test.tsx") or path.endswith(".spec.ts") or path.endswith(".spec.tsx")


def lint(repo: Path) -> list[Finding]:
    findings: list[Finding] = []
    frontend_root = repo / "frontend/src"
    if not frontend_root.exists():
        return findings

    for file_path in iter_files(frontend_root, suffixes=TS_SUFFIXES):
        rel_path = to_posix_rel(file_path, repo)
        if "/api/generated/" in rel_path:
            continue
        if _is_test_file(rel_path):
            continue

        text = file_path.read_text(encoding="utf-8")

        if rel_path != "frontend/src/api/http/client.ts":
            for match in API_LITERAL_RE.finditer(text):
                findings.append(
                    Finding(
                        rule_id="PSF001",
                        path=rel_path,
                        line=_line_number(text, match),
                        message="Direct '/api/v1/' literals are forbidden outside api/http/client.ts.",
                    )
                )

        if not rel_path.startswith("frontend/src/api/http/"):
            for pattern in (FETCH_RE, AXIOS_IMPORT_RE, AXIOS_DOT_RE):
                for match in pattern.finditer(text):
                    findings.append(
                        Finding(
                            rule_id="PSF002",
                            path=rel_path,
                            line=_line_number(text, match),
                            message=(
                                "Direct fetch/axios usage is forbidden outside frontend/src/api/http/."
                            ),
                        )
                    )

        if rel_path.startswith("frontend/src/api/domains/"):
            for match in DTO_IMPORT_RE.finditer(text):
                findings.append(
                    Finding(
                        rule_id="PSF003",
                        path=rel_path,
                        line=_line_number(text, match),
                        message=(
                            "API domain modules must not import DTOs from frontend/src/types/index.ts."
                        ),
                    )
                )

        if rel_path in INFRA_ROUTE_FILES:
            if not ROUTE_IMPORT_RE.search(text):
                findings.append(
                    Finding(
                        rule_id="PSF004",
                        path=rel_path,
                        line=1,
                        message="Infra navigation file must import route registry from config/routes.",
                    )
                )
            for pattern in HARDCODED_ROUTE_PATTERNS:
                for match in pattern.finditer(text):
                    route_literal = match.group(1)
                    if route_literal.startswith("/api/"):
                        continue
                    findings.append(
                        Finding(
                            rule_id="PSF004",
                            path=rel_path,
                            line=_line_number(text, match),
                            message=(
                                f"Hardcoded route literal '{route_literal}' is forbidden in infra "
                                "navigation files. Use config/routes."
                            ),
                        )
                    )

        if rel_path.startswith("frontend/src/hooks/"):
            for match in QUERY_KEY_LITERAL_RE.finditer(text):
                context = text[max(0, match.start() - 250):match.start()]
                if re.search(r"use(?:Infinite)?Query\s*\(\s*{", context):
                    findings.append(
                        Finding(
                            rule_id="PSF005",
                            path=rel_path,
                            line=_line_number(text, match),
                            message=(
                                "Inline query key tuples in hook query declarations are forbidden. "
                                "Use queryKeys from frontend/src/config/queryKeys.ts."
                            ),
                        )
                    )

        for match in STORAGE_CALL_RE.finditer(text):
            key = match.group(1).lower()
            if any(token in key for token in ("token", "access", "refresh", "auth")):
                findings.append(
                    Finding(
                        rule_id="PSF006",
                        path=rel_path,
                        line=_line_number(text, match),
                        message=(
                            "Browser auth token persistence in local/session storage is forbidden."
                        ),
                    )
                )

        for match in RESEARCH_GROUP_RE.finditer(text):
            findings.append(
                Finding(
                    rule_id="PSF007",
                    path=rel_path,
                    line=_line_number(text, match),
                    message="Legacy 'ResearchGroup' naming is forbidden.",
                )
            )

    for py_file in iter_files(repo / "paper_scraper", suffixes=(".py",)):
        rel_path = to_posix_rel(py_file, repo)
        text = py_file.read_text(encoding="utf-8")
        for match in RESEARCH_GROUP_RE.finditer(text):
            findings.append(
                Finding(
                    rule_id="PSF007",
                    path=rel_path,
                    line=_line_number(text, match),
                    message="Legacy 'ResearchGroup' naming is forbidden.",
                )
            )

    return findings

