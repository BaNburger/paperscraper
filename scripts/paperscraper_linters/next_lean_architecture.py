from __future__ import annotations

import json
import re
from pathlib import Path

from .common import Finding, iter_files, to_posix_rel

CODE_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")

IMPORT_SPEC_RE = re.compile(
    r"""(?:import|export)\s+(?:type\s+)?(?:[^'"]+?\s+from\s+)?['"]([^'"]+)['"]"""
)
REQUIRE_SPEC_RE = re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)""")

FETCH_RE = re.compile(r"\bfetch\s*\(")
AXIOS_RE = re.compile(r"\baxios(?:\.[A-Za-z_][A-Za-z0-9_]*)?\s*\(")
AXIOS_IMPORT_RE = re.compile(r"""(?:from|import)\s+['"]axios['"]|import\s+axios\b""")

DIRECT_DB_RE = re.compile(r"\bctx\.db\.|\bprisma\.")
RAW_SQL_RE = re.compile(r"\$queryRaw|\$queryRawUnsafe|\$executeRaw|\$executeRawUnsafe")

SELECT_STAR_RE = re.compile(r"SELECT\s+\*", re.IGNORECASE)

EVAL_RE = re.compile(r"\beval\s*\(|\bnew\s+Function\s*\(")
CHILD_PROCESS_RE = re.compile(r"\bchild_process\.(?:exec|execSync|spawn)\s*\(")
PLAIN_SECRET_RE = re.compile(r"plain:")
STORAGE_TOKEN_RE = re.compile(
    r"(?:localStorage|sessionStorage)\.(?:setItem|getItem|removeItem)\(\s*['\"]([^'\"]+)['\"]"
)

FUNCTION_DECL_RE = re.compile(r"\bfunction\s+[A-Za-z_][A-Za-z0-9_]*\s*\(")
ARROW_FUNCTION_RE = re.compile(
    r"\b(?:const|let|var)\s+[A-Za-z_][A-Za-z0-9_]*\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"
)

WORKER_RE = re.compile(r"\bnew\s+Worker\s*\(")

ENGINE_IMPORT_RE = re.compile(r"""from\s+['"][^'"]*engines/([A-Za-z0-9_-]+)""")

ROOT_CANDIDATE_NAMES = (
    "paper-scraper-next",
    "paperscraper-next",
)

NETWORK_ALLOWED_SUBPATHS = (
    "apps/web/src/api/",
    "apps/api/src/engines/ingestion/adapters/",
    "apps/api/src/providers/",
    "apps/api/src/integrations/",
    "apps/jobs/src/providers/",
    "apps/jobs/src/integrations/",
    "plugins/",
)

SINGLE_USE_DEP_ALLOWLIST = {
    "bun",
    "typescript",
    "tsx",
    "hono",
    "@hono/trpc-server",
    "@trpc/server",
    "@trpc/client",
    "@tanstack/react-start",
    "@tanstack/react-query",
    "@tanstack/react-router",
    "react",
    "react-dom",
    "@prisma/client",
    "prisma",
    "bullmq",
    "ioredis",
    "zod",
}

SHARED_COMPONENT_EXCLUDE_SUBPATHS = (
    "/components/ui/",
    "/components/icons/",
)

HELPER_NAME_RE = re.compile(r"(?:^|/)(?:helpers?|utils?)(?:/|$)|(?:helper|util)\.(?:t|j)sx?$")


def _line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _is_test_file(rel_path: str) -> bool:
    return (
        rel_path.endswith(".test.ts")
        or rel_path.endswith(".test.tsx")
        or rel_path.endswith(".spec.ts")
        or rel_path.endswith(".spec.tsx")
    )


def _iter_import_specs(text: str) -> list[tuple[str, int]]:
    specs: list[tuple[str, int]] = []
    for match in IMPORT_SPEC_RE.finditer(text):
        specs.append((match.group(1), _line_number(text, match.start())))
    for match in REQUIRE_SPEC_RE.finditer(text):
        specs.append((match.group(1), _line_number(text, match.start())))
    return specs


def _matches_dep(spec: str, dep: str) -> bool:
    return spec == dep or spec.startswith(dep + "/")


def _iter_v2_roots(repo: Path) -> list[Path]:
    roots: list[Path] = []
    for name in ROOT_CANDIDATE_NAMES:
        candidate = repo / name
        if candidate.exists() and (candidate / "apps").exists():
            roots.append(candidate)

    if not roots:
        for child in repo.iterdir():
            if (
                child.is_dir()
                and "next" in child.name.lower()
                and "paper" in child.name.lower()
                and (child / "apps").exists()
                and (child / "package.json").exists()
            ):
                roots.append(child)

    unique_roots: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        resolved = root.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique_roots.append(root)
    return unique_roots


def _build_import_usage_map(
    v2_root: Path,
) -> tuple[dict[str, int], dict[str, list[tuple[str, int]]]]:
    dep_usage: dict[str, int] = {}
    spec_occurrences: dict[str, list[tuple[str, int]]] = {}

    for source_file in iter_files(v2_root, suffixes=CODE_SUFFIXES):
        rel_path = to_posix_rel(source_file, v2_root)
        if _is_test_file(rel_path):
            continue
        text = source_file.read_text(encoding="utf-8")
        for spec, line in _iter_import_specs(text):
            dep_usage[spec] = dep_usage.get(spec, 0) + 1
            spec_occurrences.setdefault(spec, []).append((rel_path, line))

    return dep_usage, spec_occurrences


def _lint_network_boundaries(v2_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for source_file in iter_files(v2_root, suffixes=CODE_SUFFIXES):
        rel_path = to_posix_rel(source_file, v2_root)
        if _is_test_file(rel_path):
            continue
        text = source_file.read_text(encoding="utf-8")
        allowed = any(sub in rel_path for sub in NETWORK_ALLOWED_SUBPATHS)
        if allowed:
            continue
        for pattern in (FETCH_RE, AXIOS_IMPORT_RE, AXIOS_RE):
            for match in pattern.finditer(text):
                findings.append(
                    Finding(
                        rule_id="PSN001",
                        path=f"{v2_root.name}/{rel_path}",
                        line=_line_number(text, match.start()),
                        message=(
                            "Ad hoc network calls are forbidden outside approved API/adapter/provider "
                            "boundaries."
                        ),
                    )
                )
    return findings


def _lint_router_boundaries(v2_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    routers_root = v2_root / "apps/api/src/routers"
    if not routers_root.exists():
        return findings

    for router_file in iter_files(routers_root, suffixes=(".ts",)):
        rel_path = to_posix_rel(router_file, v2_root)
        text = router_file.read_text(encoding="utf-8")

        for pattern in (DIRECT_DB_RE, RAW_SQL_RE):
            for match in pattern.finditer(text):
                findings.append(
                    Finding(
                        rule_id="PSN002",
                        path=f"{v2_root.name}/{rel_path}",
                        line=_line_number(text, match.start()),
                        message=(
                            "Router-level direct DB/raw SQL usage is forbidden. Routers must call "
                            "engine public APIs only."
                        ),
                    )
                )
    return findings


def _lint_engine_import_boundaries(v2_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    engines_root = v2_root / "apps/api/src/engines"
    if not engines_root.exists():
        return findings

    for engine_file in iter_files(engines_root, suffixes=(".ts",)):
        rel_path = to_posix_rel(engine_file, v2_root)
        parts = rel_path.split("/")
        if len(parts) < 6:
            continue
        # apps/api/src/engines/<engine>/...
        current_engine = parts[4]
        if current_engine in {"shared", "common"}:
            continue
        text = engine_file.read_text(encoding="utf-8")
        for match in ENGINE_IMPORT_RE.finditer(text):
            target_engine = match.group(1)
            if target_engine in {current_engine, "shared", "common"}:
                continue
            findings.append(
                Finding(
                    rule_id="PSN003",
                    path=f"{v2_root.name}/{rel_path}",
                    line=_line_number(text, match.start()),
                    message=(
                        f"Cross-engine import from '{current_engine}' to '{target_engine}' is forbidden. "
                        "Use queue/event contracts."
                    ),
                )
            )
    return findings


def _lint_dependency_reuse(v2_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    package_json_path = v2_root / "package.json"
    if not package_json_path.exists():
        return findings

    raw_text = package_json_path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        findings.append(
            Finding(
                rule_id="PSN004",
                path=f"{v2_root.name}/package.json",
                line=1,
                message="Invalid package.json format. Cannot enforce dependency reuse constraints.",
            )
        )
        return findings

    dependencies: dict[str, str] = data.get("dependencies") or {}
    if not dependencies:
        return findings

    _, occurrences = _build_import_usage_map(v2_root)
    usage_count: dict[str, int] = {}
    for dep in dependencies:
        count = 0
        for spec, refs in occurrences.items():
            if _matches_dep(spec, dep):
                count += len(refs)
        usage_count[dep] = count

    for dep, count in usage_count.items():
        if dep in SINGLE_USE_DEP_ALLOWLIST:
            continue
        dep_idx = raw_text.find(f'"{dep}"')
        line = _line_number(raw_text, dep_idx) if dep_idx >= 0 else 1
        if count == 0:
            findings.append(
                Finding(
                    rule_id="PSN004",
                    path=f"{v2_root.name}/package.json",
                    line=line,
                    message=(
                        f"Dependency '{dep}' is declared but unused. Remove it to keep the stack lean."
                    ),
                )
            )
        elif count == 1:
            findings.append(
                Finding(
                    rule_id="PSN004",
                    path=f"{v2_root.name}/package.json",
                    line=line,
                    message=(
                        f"Dependency '{dep}' appears only once. Single-use libraries are forbidden "
                        "unless explicitly allowlisted."
                    ),
                )
            )

    return findings


def _count_import_refs_for_module(v2_root: Path, module_suffix: str) -> int:
    count = 0
    suffix = module_suffix.replace("\\", "/")
    for source_file in iter_files(v2_root, suffixes=CODE_SUFFIXES):
        rel_path = to_posix_rel(source_file, v2_root)
        text = source_file.read_text(encoding="utf-8")
        if suffix in rel_path:
            continue
        for spec, _line in _iter_import_specs(text):
            normalized = spec.replace("\\", "/")
            if suffix in normalized or normalized.endswith(suffix):
                count += 1
    return count


def _lint_shared_component_reuse(v2_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    components_root = v2_root / "apps/web/src/components"
    if not components_root.exists():
        return findings

    for component_file in iter_files(components_root, suffixes=(".ts", ".tsx")):
        rel_path = to_posix_rel(component_file, v2_root)
        if _is_test_file(rel_path):
            continue
        if rel_path.endswith("/index.ts") or rel_path.endswith("/index.tsx"):
            continue
        if any(ex in rel_path for ex in SHARED_COMPONENT_EXCLUDE_SUBPATHS):
            continue

        module_suffix = rel_path.split("apps/web/src/", 1)[1]
        module_suffix = re.sub(r"\.(?:ts|tsx)$", "", module_suffix)
        refs = _count_import_refs_for_module(v2_root, module_suffix)
        if refs < 2:
            findings.append(
                Finding(
                    rule_id="PSN005",
                    path=f"{v2_root.name}/{rel_path}",
                    line=1,
                    message=(
                        "Shared component is referenced fewer than 2 times. Single-use UI elements "
                        "belong next to the feature, not in shared components."
                    ),
                )
            )

    return findings


def _lint_helper_file_reuse(v2_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for source_file in iter_files(v2_root, suffixes=CODE_SUFFIXES):
        rel_path = to_posix_rel(source_file, v2_root)
        if not HELPER_NAME_RE.search(rel_path):
            continue
        if _is_test_file(rel_path):
            continue
        module_suffix = rel_path
        module_suffix = re.sub(r"\.(?:ts|tsx|js|jsx|mjs|cjs)$", "", module_suffix)
        refs = _count_import_refs_for_module(v2_root, module_suffix)
        if refs < 2:
            findings.append(
                Finding(
                    rule_id="PSN006",
                    path=f"{v2_root.name}/{rel_path}",
                    line=1,
                    message=(
                        "Ad hoc helper/utility file has fewer than 2 import sites. Inline it into the "
                        "owning module or create a truly shared abstraction."
                    ),
                )
            )
    return findings


def _lint_file_size_and_function_density(v2_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for source_file in iter_files(v2_root, suffixes=CODE_SUFFIXES):
        rel_path = to_posix_rel(source_file, v2_root)
        if _is_test_file(rel_path):
            continue
        text = source_file.read_text(encoding="utf-8")
        line_count = len(text.splitlines())

        if rel_path.startswith("apps/api/src/") or rel_path.startswith("apps/jobs/src/"):
            if line_count > 420:
                findings.append(
                    Finding(
                        rule_id="PSN007",
                        path=f"{v2_root.name}/{rel_path}",
                        line=1,
                        message=(
                            f"File has {line_count} lines (>420). Keep modules compact for readability "
                            "and security reviewability."
                        ),
                    )
                )
            max_functions = 12
        elif rel_path.startswith("apps/web/src/"):
            if line_count > 320:
                findings.append(
                    Finding(
                        rule_id="PSN007",
                        path=f"{v2_root.name}/{rel_path}",
                        line=1,
                        message=(
                            f"File has {line_count} lines (>320). Keep frontend modules compact to avoid "
                            "UI clutter and maintenance bloat."
                        ),
                    )
                )
            max_functions = 10
        elif rel_path.startswith("packages/shared/src/"):
            if line_count > 260:
                findings.append(
                    Finding(
                        rule_id="PSN007",
                        path=f"{v2_root.name}/{rel_path}",
                        line=1,
                        message=(
                            f"Shared file has {line_count} lines (>260). Keep shared contracts minimal."
                        ),
                    )
                )
            max_functions = 10
        else:
            max_functions = 14

        function_count = len(FUNCTION_DECL_RE.findall(text)) + len(ARROW_FUNCTION_RE.findall(text))
        if function_count > max_functions:
            findings.append(
                Finding(
                    rule_id="PSN010",
                    path=f"{v2_root.name}/{rel_path}",
                    line=1,
                    message=(
                        f"File defines {function_count} functions (> {max_functions}). Avoid ad hoc "
                        "function sprawl; split by cohesive responsibility."
                    ),
                )
            )

    return findings


def _lint_security_and_sql_patterns(v2_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for source_file in iter_files(v2_root, suffixes=CODE_SUFFIXES):
        rel_path = to_posix_rel(source_file, v2_root)
        if _is_test_file(rel_path):
            continue
        text = source_file.read_text(encoding="utf-8")

        for pattern in (EVAL_RE, CHILD_PROCESS_RE, RAW_SQL_RE):
            for match in pattern.finditer(text):
                findings.append(
                    Finding(
                        rule_id="PSN008",
                        path=f"{v2_root.name}/{rel_path}",
                        line=_line_number(text, match.start()),
                        message=(
                            "Unsafe primitive detected (eval/dynamic execution/raw SQL unsafe path). "
                            "Use safe, typed abstractions."
                        ),
                    )
                )

        for match in SELECT_STAR_RE.finditer(text):
            findings.append(
                Finding(
                    rule_id="PSN009",
                    path=f"{v2_root.name}/{rel_path}",
                    line=_line_number(text, match.start()),
                    message="`SELECT *` is forbidden in v2. Explicit projections are required.",
                )
            )

        for match in PLAIN_SECRET_RE.finditer(text):
            findings.append(
                Finding(
                    rule_id="PSN008",
                    path=f"{v2_root.name}/{rel_path}",
                    line=_line_number(text, match.start()),
                    message="Legacy secret format `plain:` is forbidden.",
                )
            )

        for match in STORAGE_TOKEN_RE.finditer(text):
            key = match.group(1).lower()
            if any(t in key for t in ("token", "access", "refresh", "auth")):
                findings.append(
                    Finding(
                        rule_id="PSN008",
                        path=f"{v2_root.name}/{rel_path}",
                        line=_line_number(text, match.start()),
                        message="Auth tokens must not be stored in browser storage.",
                    )
                )
    return findings


def _lint_worker_contracts(v2_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    jobs_root = v2_root / "apps/jobs/src"
    if not jobs_root.exists():
        return findings

    for worker_file in iter_files(jobs_root, suffixes=(".ts", ".js", ".mjs", ".cjs")):
        rel_path = to_posix_rel(worker_file, v2_root)
        text = worker_file.read_text(encoding="utf-8")
        if not WORKER_RE.search(text):
            continue
        if "concurrency:" not in text:
            findings.append(
                Finding(
                    rule_id="PSN009",
                    path=f"{v2_root.name}/{rel_path}",
                    line=1,
                    message="Worker missing explicit concurrency setting.",
                )
            )
        if "backoff" not in text and "attempts" not in text:
            findings.append(
                Finding(
                    rule_id="PSN009",
                    path=f"{v2_root.name}/{rel_path}",
                    line=1,
                    message="Worker/queue file missing explicit retry policy (attempts/backoff).",
                )
            )
    return findings


def lint(repo: Path) -> list[Finding]:
    findings: list[Finding] = []
    for v2_root in _iter_v2_roots(repo):
        findings.extend(_lint_network_boundaries(v2_root))
        findings.extend(_lint_router_boundaries(v2_root))
        findings.extend(_lint_engine_import_boundaries(v2_root))
        findings.extend(_lint_dependency_reuse(v2_root))
        findings.extend(_lint_shared_component_reuse(v2_root))
        findings.extend(_lint_helper_file_reuse(v2_root))
        findings.extend(_lint_file_size_and_function_density(v2_root))
        findings.extend(_lint_security_and_sql_patterns(v2_root))
        findings.extend(_lint_worker_contracts(v2_root))
    return findings
