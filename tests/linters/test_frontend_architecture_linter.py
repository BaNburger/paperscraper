from __future__ import annotations

from pathlib import Path

from scripts.paperscraper_linters import frontend_architecture


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _has_rule(findings, rule_id: str) -> bool:
    return any(f.rule_id == rule_id for f in findings)


def test_psf001_flags_direct_api_v1_literals(tmp_path: Path) -> None:
    _write(tmp_path / "frontend/src/foo.ts", "const x = '/api/v1/papers'\n")
    findings = frontend_architecture.lint(tmp_path)
    assert _has_rule(findings, "PSF001")


def test_psf002_flags_fetch_outside_http_client(tmp_path: Path) -> None:
    _write(tmp_path / "frontend/src/pages/Foo.tsx", "fetch('/x')\n")
    findings = frontend_architecture.lint(tmp_path)
    assert _has_rule(findings, "PSF002")


def test_psf003_flags_domain_import_from_types_index(tmp_path: Path) -> None:
    _write(
        tmp_path / "frontend/src/api/domains/papers.ts",
        "import type { Paper } from '@/types/index'\n",
    )
    findings = frontend_architecture.lint(tmp_path)
    assert _has_rule(findings, "PSF003")


def test_psf004_flags_hardcoded_route_literals_in_infra_file(tmp_path: Path) -> None:
    _write(
        tmp_path / "frontend/src/hooks/useKeyboardShortcuts.ts",
        "import { NAVIGATION_SHORTCUTS } from '@/config/routes'\nnavigate('/papers')\n",
    )
    findings = frontend_architecture.lint(tmp_path)
    assert _has_rule(findings, "PSF004")


def test_psf005_flags_inline_query_key_tuples_in_hooks(tmp_path: Path) -> None:
    _write(
        tmp_path / "frontend/src/hooks/useFoo.ts",
        "function useFoo(){ return useQuery({ queryKey: ['foo'], queryFn: async () => [] }) }\n",
    )
    findings = frontend_architecture.lint(tmp_path)
    assert _has_rule(findings, "PSF005")


def test_psf006_flags_auth_token_storage_keys(tmp_path: Path) -> None:
    _write(
        tmp_path / "frontend/src/contexts/Auth.tsx",
        "localStorage.setItem('auth_token', token)\n",
    )
    findings = frontend_architecture.lint(tmp_path)
    assert _has_rule(findings, "PSF006")


def test_psf007_flags_research_group_legacy_naming(tmp_path: Path) -> None:
    _write(tmp_path / "frontend/src/pages/ProjectsPage.tsx", "const label = 'ResearchGroup'\n")
    findings = frontend_architecture.lint(tmp_path)
    assert _has_rule(findings, "PSF007")
