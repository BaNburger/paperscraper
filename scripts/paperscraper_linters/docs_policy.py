from __future__ import annotations

import re
from pathlib import Path

from .common import Finding, to_posix_rel

CLAUDE_RULES_HEADING = "Linter-Enforced Architecture Rules"
AGENTS_REQUIRED_SECTIONS = (
    "Scope and Precedence",
    "Non-Negotiables",
    "Mandatory Workflow",
    "Forbidden Patterns",
    "Exception Process",
)


def _line_for(text: str, needle: str) -> int:
    index = text.find(needle)
    if index < 0:
        return 1
    return text.count("\n", 0, index) + 1


def _has_heading(text: str, heading: str) -> bool:
    pattern = re.compile(rf"^#+\s+{re.escape(heading)}\s*$", re.MULTILINE)
    return bool(pattern.search(text))


def _validate_doc_command_policy(
    findings: list[Finding],
    *,
    doc_path: Path,
    repo: Path,
    text: str,
) -> None:
    rel_path = to_posix_rel(doc_path, repo)
    if "npm run lint:agents" not in text:
        findings.append(
            Finding(
                rule_id="PSD003",
                path=rel_path,
                line=1,
                message="Document must include linter command: npm run lint:agents.",
            )
        )
    if ".agent-lint-allowlist.yaml" not in text:
        findings.append(
            Finding(
                rule_id="PSD003",
                path=rel_path,
                line=1,
                message="Document must include allowlist workflow: .agent-lint-allowlist.yaml.",
            )
        )


def lint(repo: Path) -> list[Finding]:
    findings: list[Finding] = []

    claude_path = repo / "CLAUDE.md"
    agents_path = repo / "AGENTS.md"

    if not claude_path.exists():
        findings.append(
            Finding(
                rule_id="PSD001",
                path="CLAUDE.md",
                line=1,
                message="CLAUDE.md is missing.",
            )
        )
    else:
        claude_text = claude_path.read_text(encoding="utf-8")
        if not _has_heading(claude_text, CLAUDE_RULES_HEADING):
            findings.append(
                Finding(
                    rule_id="PSD001",
                    path="CLAUDE.md",
                    line=1,
                    message=(
                        f"CLAUDE.md must contain a '{CLAUDE_RULES_HEADING}' section."
                    ),
                )
            )
        _validate_doc_command_policy(
            findings,
            doc_path=claude_path,
            repo=repo,
            text=claude_text,
        )

    if not agents_path.exists():
        findings.append(
            Finding(
                rule_id="PSD002",
                path="AGENTS.md",
                line=1,
                message="AGENTS.md is required for Codex agents.",
            )
        )
    else:
        agents_text = agents_path.read_text(encoding="utf-8")
        for section in AGENTS_REQUIRED_SECTIONS:
            if section not in agents_text:
                findings.append(
                    Finding(
                        rule_id="PSD002",
                        path="AGENTS.md",
                        line=_line_for(agents_text, section),
                        message=f"AGENTS.md missing required section: '{section}'.",
                    )
                )
        _validate_doc_command_policy(
            findings,
            doc_path=agents_path,
            repo=repo,
            text=agents_text,
        )

    return findings

