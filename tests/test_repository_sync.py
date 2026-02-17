"""Unit tests for repository sync scheduling helpers."""

from datetime import UTC, datetime

from paper_scraper.jobs.repository_sync import _schedule_is_due


def test_schedule_is_due_exact_match() -> None:
    """Exact cron timestamp should match."""
    ts = datetime(2026, 2, 9, 6, 0, tzinfo=UTC)
    assert _schedule_is_due("0 6 * * *", ts)


def test_schedule_is_due_step_match() -> None:
    """Step expressions should match expected minutes."""
    ts = datetime(2026, 2, 9, 6, 30, tzinfo=UTC)
    assert _schedule_is_due("*/30 * * * *", ts)
    assert not _schedule_is_due("*/20 * * * *", ts)


def test_schedule_is_due_sunday_alias() -> None:
    """Sunday should match both 0 and 7 cron representations."""
    sunday = datetime(2026, 2, 8, 12, 0, tzinfo=UTC)  # Sunday
    assert _schedule_is_due("0 12 * * 0", sunday)
    assert _schedule_is_due("0 12 * * 7", sunday)
