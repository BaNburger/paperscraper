from __future__ import annotations

import datetime as dt
import fnmatch
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

ROUTER_DECORATOR_RE = re.compile(
    r"@router\.(?:get|post|put|patch|delete)\(\s*[\"']([^\"']+)[\"']",
    re.MULTILINE,
)

DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "dist",
    "build",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "playwright-report",
    "test-results",
    "__pycache__",
}

INLINE_IGNORE_MARKERS = (
    "paperscraper-lint: ignore",
    "agent-lint: ignore",
    "pslint-ignore",
    "pslint: ignore",
)


@dataclass(frozen=True)
class Finding:
    rule_id: str
    path: str
    line: int
    message: str
    severity: str = "error"

    def to_text(self) -> str:
        return f"{self.rule_id} {self.path}:{self.line} {self.message}"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AllowlistEntry:
    rule_id: str
    path: str
    match: str
    reason: str
    owner: str
    expires_on: dt.date


def to_posix_rel(path: Path, repo: Path) -> str:
    return path.resolve().relative_to(repo.resolve()).as_posix()


def line_number_from_index(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def iter_files(
    root: Path,
    suffixes: tuple[str, ...],
    exclude_dirs: set[str] | None = None,
) -> Iterable[Path]:
    excluded = DEFAULT_EXCLUDE_DIRS | (exclude_dirs or set())
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in suffixes:
            continue
        if any(part in excluded for part in path.parts):
            continue
        yield path


def iter_router_routes(text: str) -> Iterable[tuple[str, int]]:
    for match in ROUTER_DECORATOR_RE.finditer(text):
        yield match.group(1), line_number_from_index(text, match.start())


def _strip_inline_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for idx, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if char == "#" and not in_single and not in_double:
            return line[:idx]
    return line


def _parse_key_value(chunk: str) -> tuple[str, str]:
    if ":" not in chunk:
        raise ValueError(f"Invalid allowlist line (missing ':'): {chunk}")
    key, raw_value = chunk.split(":", 1)
    key = key.strip()
    value = raw_value.strip()
    if not key:
        raise ValueError(f"Invalid allowlist key: {chunk}")
    if len(value) >= 2 and value[0] in {"'", '"'} and value[-1] == value[0]:
        value = value[1:-1]
    return key, value


def _parse_simple_yaml_list(content: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    for raw_line in content.splitlines():
        line = _strip_inline_comment(raw_line).rstrip()
        if not line.strip():
            continue
        stripped = line.lstrip()

        if stripped.startswith("- "):
            if current is not None:
                entries.append(current)
            current = {}
            remainder = stripped[2:].strip()
            if remainder:
                key, value = _parse_key_value(remainder)
                current[key] = value
            continue

        if current is None:
            raise ValueError(
                "Allowlist YAML must start with '-' list items "
                "(see .agent-lint-allowlist.yaml schema)."
            )

        key, value = _parse_key_value(stripped)
        current[key] = value

    if current is not None:
        entries.append(current)
    return entries


def load_allowlist(repo: Path) -> tuple[list[AllowlistEntry], list[Finding]]:
    allowlist_path = repo / ".agent-lint-allowlist.yaml"
    findings: list[Finding] = []

    if not allowlist_path.exists():
        findings.append(
            Finding(
                rule_id="PSL001",
                path=".agent-lint-allowlist.yaml",
                line=1,
                message="Allowlist file is missing. Create .agent-lint-allowlist.yaml.",
            )
        )
        return [], findings

    try:
        raw_entries = _parse_simple_yaml_list(allowlist_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - validated by test suite
        findings.append(
            Finding(
                rule_id="PSL001",
                path=".agent-lint-allowlist.yaml",
                line=1,
                message=f"Failed to parse allowlist YAML: {exc}",
            )
        )
        return [], findings

    entries: list[AllowlistEntry] = []
    required = {"rule_id", "path", "match", "reason", "owner", "expires_on"}
    today = dt.date.today()

    for index, raw_entry in enumerate(raw_entries, start=1):
        missing = sorted(required - raw_entry.keys())
        if missing:
            findings.append(
                Finding(
                    rule_id="PSL001",
                    path=".agent-lint-allowlist.yaml",
                    line=index,
                    message=f"Allowlist entry missing required fields: {', '.join(missing)}",
                )
            )
            continue

        expires_raw = raw_entry["expires_on"]
        try:
            expires_on = dt.date.fromisoformat(expires_raw)
        except ValueError:
            findings.append(
                Finding(
                    rule_id="PSL002",
                    path=".agent-lint-allowlist.yaml",
                    line=index,
                    message=f"Invalid expires_on date '{expires_raw}'. Use YYYY-MM-DD.",
                )
            )
            continue

        if expires_on < today:
            findings.append(
                Finding(
                    rule_id="PSL002",
                    path=".agent-lint-allowlist.yaml",
                    line=index,
                    message=(
                        f"Expired allowlist entry for {raw_entry['rule_id']} "
                        f"({raw_entry['path']}) on {expires_on.isoformat()}."
                    ),
                )
            )
            continue

        try:
            re.compile(raw_entry["match"])
        except re.error as exc:
            findings.append(
                Finding(
                    rule_id="PSL001",
                    path=".agent-lint-allowlist.yaml",
                    line=index,
                    message=f"Invalid match regex '{raw_entry['match']}': {exc}",
                )
            )
            continue

        entries.append(
            AllowlistEntry(
                rule_id=raw_entry["rule_id"],
                path=raw_entry["path"],
                match=raw_entry["match"],
                reason=raw_entry["reason"],
                owner=raw_entry["owner"],
                expires_on=expires_on,
            )
        )

    return entries, findings


def is_allowlisted(finding: Finding, allowlist: list[AllowlistEntry]) -> bool:
    for entry in allowlist:
        if entry.rule_id != finding.rule_id:
            continue
        if not fnmatch.fnmatch(finding.path, entry.path):
            continue
        if re.search(entry.match, finding.message):
            return True
    return False


def find_inline_ignore_markers(repo: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_files(
        root=repo,
        suffixes=(".py", ".ts", ".tsx", ".md", ".yaml", ".yml"),
    ):
        text = path.read_text(encoding="utf-8")
        rel_path = to_posix_rel(path, repo)
        for line_no, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            for marker in INLINE_IGNORE_MARKERS:
                is_comment_line = "#" in line or "//" in line or "/*" in line
                if marker in lowered and is_comment_line:
                    findings.append(
                        Finding(
                            rule_id="PSL003",
                            path=rel_path,
                            line=line_no,
                            message=(
                                "Inline lint suppressions are forbidden. "
                                "Use .agent-lint-allowlist.yaml."
                            ),
                        )
                    )
    return findings
