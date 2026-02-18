from __future__ import annotations

from pathlib import Path

from scripts.paperscraper_linters import python_architecture


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _has_rule(findings, rule_id: str) -> bool:
    return any(f.rule_id == rule_id for f in findings)


def test_psa001_flags_source_routes_in_papers_router(tmp_path: Path) -> None:
    _write(
        tmp_path / "paper_scraper/modules/papers/router.py",
        '@router.post("/sources/openalex/runs")\nasync def x():\n    pass\n',
    )

    findings = python_architecture.lint(tmp_path)
    assert _has_rule(findings, "PSA001")


def test_psa002_flags_source_run_routes_outside_ingestion(tmp_path: Path) -> None:
    _write(
        tmp_path / "paper_scraper/modules/other/router.py",
        '@router.post("/sources/pubmed/runs")\nasync def x():\n    pass\n',
    )
    _write(
        tmp_path / "paper_scraper/modules/ingestion/router.py",
        '@router.post("/sources/pubmed/runs")\nasync def x():\n    pass\n',
    )

    findings = python_architecture.lint(tmp_path)
    assert _has_rule(findings, "PSA002")


def test_psa003_flags_direct_storage_sdk_usage(tmp_path: Path) -> None:
    _write(
        tmp_path / "paper_scraper/modules/papers/pdf_service.py",
        "import boto3\nclient = boto3.client('s3')\n",
    )
    _write(tmp_path / "paper_scraper/core/storage.py", "import boto3\n")

    findings = python_architecture.lint(tmp_path)
    assert _has_rule(findings, "PSA003")


def test_psa004_flags_private_service_method_calls_in_router(tmp_path: Path) -> None:
    _write(
        tmp_path / "paper_scraper/modules/foo/router.py",
        "async def route(service):\n    return await service._hidden_call()\n",
    )

    findings = python_architecture.lint(tmp_path)
    assert _has_rule(findings, "PSA004")


def test_psa005_flags_plain_secret_marker(tmp_path: Path) -> None:
    _write(
        tmp_path / "paper_scraper/modules/scoring/service.py",
        "value = 'plain:my-secret'\n",
    )
    _write(
        tmp_path / "paper_scraper/modules/model_settings/service.py",
        "value = 'enc:v1:abc'\n",
    )

    findings = python_architecture.lint(tmp_path)
    assert _has_rule(findings, "PSA005")

