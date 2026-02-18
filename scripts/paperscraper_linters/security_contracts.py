from __future__ import annotations

from pathlib import Path

from .common import Finding, find_inline_ignore_markers


def lint(repo: Path) -> list[Finding]:
    """Security and policy contract checks."""
    return find_inline_ignore_markers(repo)

