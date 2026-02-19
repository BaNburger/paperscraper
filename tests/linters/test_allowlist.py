from __future__ import annotations

import datetime as dt
from pathlib import Path

from scripts.paperscraper_linters.common import Finding, is_allowlisted, load_allowlist


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_allowlist_entry_missing_metadata_fails(tmp_path: Path) -> None:
    _write(
        tmp_path / ".agent-lint-allowlist.yaml",
        "- rule_id: PSF001\n"
        "  path: frontend/src/foo.ts\n"
        "  match: forbidden\n"
        "  reason: missing owner and expires\n",
    )

    entries, findings = load_allowlist(tmp_path)
    assert entries == []
    assert any(f.rule_id == "PSL001" for f in findings)


def test_expired_allowlist_entry_fails(tmp_path: Path) -> None:
    _write(
        tmp_path / ".agent-lint-allowlist.yaml",
        "- rule_id: PSF001\n"
        "  path: frontend/src/foo.ts\n"
        "  match: forbidden\n"
        "  reason: temporary\n"
        "  owner: team\n"
        "  expires_on: 2000-01-01\n",
    )

    entries, findings = load_allowlist(tmp_path)
    assert entries == []
    assert any(f.rule_id == "PSL002" for f in findings)


def test_valid_allowlist_entry_is_applied(tmp_path: Path) -> None:
    future = (dt.date.today() + dt.timedelta(days=365)).isoformat()
    _write(
        tmp_path / ".agent-lint-allowlist.yaml",
        "- rule_id: PSF007\n"
        "  path: frontend/src/pages/ProjectsPage.tsx\n"
        "  match: ResearchGroup\n"
        "  reason: migration\n"
        "  owner: frontend\n"
        f"  expires_on: {future}\n",
    )

    entries, findings = load_allowlist(tmp_path)
    assert findings == []
    finding = Finding(
        rule_id="PSF007",
        path="frontend/src/pages/ProjectsPage.tsx",
        line=10,
        message="Legacy 'ResearchGroup' naming is forbidden.",
    )
    assert is_allowlisted(finding, entries)
