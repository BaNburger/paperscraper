from __future__ import annotations

from pathlib import Path

from scripts.paperscraper_linters import run


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _seed_docs(repo: Path) -> None:
    _write(
        repo / "CLAUDE.md",
        "## Linter-Enforced Architecture Rules\n"
        "- Run `npm run lint:agents`\n"
        "- Exception workflow uses `.agent-lint-allowlist.yaml`\n",
    )
    _write(
        repo / "AGENTS.md",
        "## Scope and Precedence\n"
        "## Non-Negotiables\n"
        "## Mandatory Workflow\n"
        "- Run `npm run lint:agents`\n"
        "## Forbidden Patterns\n"
        "## Exception Process\n"
        "- Use `.agent-lint-allowlist.yaml`\n",
    )
    _write(repo / ".agent-lint-allowlist.yaml", "")


def test_runner_fails_for_simulated_violation(tmp_path: Path) -> None:
    _seed_docs(tmp_path)
    _write(tmp_path / "frontend/src/pages/Foo.tsx", "fetch('/x')\n")

    code = run.main(["--repo", str(tmp_path), "--mode", "ci", "--format", "text"])
    assert code == 1


def test_runner_passes_for_clean_repo_fixture(tmp_path: Path) -> None:
    _seed_docs(tmp_path)

    code = run.main(["--repo", str(tmp_path), "--mode", "ci", "--format", "json"])
    assert code == 0


def test_ci_workflow_contains_agent_lint_step() -> None:
    repo = Path(__file__).resolve().parents[2]
    ci = (repo / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "python scripts/paperscraper_linters/run.py --repo . --mode ci --format text" in ci

