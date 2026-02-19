from __future__ import annotations

from pathlib import Path

from scripts.paperscraper_linters import docs_policy


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_docs_policy_flags_missing_required_sections(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "# Claude\n")
    _write(tmp_path / "AGENTS.md", "# Agents\n")

    findings = docs_policy.lint(tmp_path)
    rule_ids = {finding.rule_id for finding in findings}
    assert "PSD001" in rule_ids
    assert "PSD002" in rule_ids
    assert "PSD003" in rule_ids


def test_docs_policy_passes_with_required_sections(tmp_path: Path) -> None:
    _write(
        tmp_path / "CLAUDE.md",
        "## Linter-Enforced Architecture Rules\n"
        "- Run `npm run lint:agents`\n"
        "- Exceptions in `.agent-lint-allowlist.yaml`\n",
    )
    _write(
        tmp_path / "AGENTS.md",
        "## Scope and Precedence\n"
        "## Non-Negotiables\n"
        "## Mandatory Workflow\n"
        "- Run `npm run lint:agents`\n"
        "## Forbidden Patterns\n"
        "## Exception Process\n"
        "- Use `.agent-lint-allowlist.yaml`\n",
    )

    findings = docs_policy.lint(tmp_path)
    assert findings == []
