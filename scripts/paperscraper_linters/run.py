#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

if __package__ in {None, ""}:
    script_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(script_dir.parent))
    from paperscraper_linters import (  # type: ignore[import-not-found]
        docs_policy,
        frontend_architecture,
        python_architecture,
        security_contracts,
    )
    from paperscraper_linters.common import (  # type: ignore[import-not-found]
        AllowlistEntry,
        Finding,
        is_allowlisted,
        load_allowlist,
    )
else:
    from . import docs_policy, frontend_architecture, python_architecture, security_contracts
    from .common import AllowlistEntry, Finding, is_allowlisted, load_allowlist


NON_SUPPRESSIBLE_PREFIXES = ("PSL",)


def collect_findings(repo: Path) -> tuple[list[Finding], list[AllowlistEntry]]:
    allowlist_entries, allowlist_findings = load_allowlist(repo)

    findings: list[Finding] = []
    findings.extend(allowlist_findings)
    findings.extend(python_architecture.lint(repo))
    findings.extend(frontend_architecture.lint(repo))
    findings.extend(security_contracts.lint(repo))
    findings.extend(docs_policy.lint(repo))

    return findings, allowlist_entries


def apply_allowlist(
    findings: Sequence[Finding],
    allowlist_entries: Sequence[AllowlistEntry],
) -> list[Finding]:
    filtered: list[Finding] = []
    for finding in findings:
        if finding.rule_id.startswith(NON_SUPPRESSIBLE_PREFIXES):
            filtered.append(finding)
            continue
        if is_allowlisted(finding, list(allowlist_entries)):
            continue
        filtered.append(finding)
    return filtered


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PaperScraper strict agent linter suite.")
    parser.add_argument("--repo", default=".", help="Repository root path.")
    parser.add_argument("--mode", choices=("ci", "local"), default="local")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--fail-on-warn",
        dest="fail_on_warn",
        action="store_true",
        default=None,
        help="Fail on warnings.",
    )
    parser.add_argument(
        "--no-fail-on-warn",
        dest="fail_on_warn",
        action="store_false",
        default=None,
        help="Do not fail on warnings.",
    )
    return parser.parse_args(argv)


def _print_findings(findings: Sequence[Finding], output_format: str) -> None:
    ordered = sorted(findings, key=lambda f: (f.path, f.line, f.rule_id, f.message))
    if output_format == "json":
        payload = [finding.to_dict() for finding in ordered]
        print(json.dumps(payload, indent=2))
        return
    for finding in ordered:
        print(finding.to_text())


def _exit_code(findings: Sequence[Finding], fail_on_warn: bool) -> int:
    has_error = any(finding.severity == "error" for finding in findings)
    has_warn = any(finding.severity == "warn" for finding in findings)
    if has_error:
        return 1
    if has_warn and fail_on_warn:
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo = Path(args.repo).resolve()
    if args.fail_on_warn is None:
        fail_on_warn = args.mode == "ci"
    else:
        fail_on_warn = bool(args.fail_on_warn)

    findings, allowlist_entries = collect_findings(repo)
    filtered = apply_allowlist(findings, allowlist_entries)
    _print_findings(filtered, args.format)
    return _exit_code(filtered, fail_on_warn)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
