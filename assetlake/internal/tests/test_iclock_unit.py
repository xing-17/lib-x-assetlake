"""Unit tests for IClock."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from assetlake.internal.iclock import IClock

_UTC = ZoneInfo("UTC")
_TOKYO = ZoneInfo("Asia/Tokyo")
_NY = ZoneInfo("America/New_York")


def test_from_datetime_with_tz_aware():
    """Test from_datetime with tz-aware datetime converts to UTC."""
    tokyo_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=_TOKYO)
    result = IClock.from_datetime(tokyo_time)
    assert result.tzinfo == _UTC
    assert result == datetime(2024, 1, 15, 3, 0, 0, tzinfo=_UTC)


def test_from_datetime_with_naive():
    """Test from_datetime with naive datetime assumes UTC."""
    naive_time = datetime(2024, 1, 15, 12, 0, 0)
    result = IClock.from_datetime(naive_time)
    assert result.tzinfo == _UTC
    assert result == datetime(2024, 1, 15, 12, 0, 0, tzinfo=_UTC)


def test_from_iso_with_tz_aware():
    """Test from_iso with tz-aware ISO string converts to UTC."""
    iso_string = "2024-01-15T12:00:00+09:00"
    result = IClock.from_iso(iso_string)
    assert result.tzinfo == _UTC
    assert result == datetime(2024, 1, 15, 3, 0, 0, tzinfo=_UTC)


def test_from_iso_with_naive():
    """Test from_iso with naive ISO string assumes UTC."""
    iso_string = "2024-01-15T12:00:00"
    result = IClock.from_iso(iso_string)
    assert result.tzinfo == _UTC
    assert result == datetime(2024, 1, 15, 12, 0, 0, tzinfo=_UTC)


def test_from_iso_with_empty_string():
    """Test from_iso with empty string returns None."""
    result = IClock.from_iso("")
    assert result is None


def test_from_iso_with_utc_z_suffix():
    """Test from_iso with Z suffix (UTC)."""
    iso_string = "2024-01-15T12:00:00Z"
    result = IClock.from_iso(iso_string)
    assert result.tzinfo == _UTC
    assert result == datetime(2024, 1, 15, 12, 0, 0, tzinfo=_UTC)


def test_from_timestamp():
    """Test from_timestamp always returns UTC tz-aware datetime."""
    timestamp = 1705320000.0
    result = IClock.from_timestamp(timestamp)
    assert result.tzinfo == _UTC
    expected = datetime(2024, 1, 15, 12, 0, 0, tzinfo=_UTC)
    assert result == expected


def test_from_timestamp_zero():
    """Test from_timestamp with epoch zero."""
    result = IClock.from_timestamp(0.0)
    assert result.tzinfo == _UTC
    assert result == datetime(1970, 1, 1, 0, 0, 0, tzinfo=_UTC)


def test_current():
    """Test current returns UTC tz-aware datetime."""
    result = IClock.current()
    assert result.tzinfo == _UTC
    assert isinstance(result, datetime)


def test_current_iso():
    """Test current_iso returns ISO string."""
    result = IClock.current_iso()
    assert isinstance(result, str)
    assert "T" in result
    parsed = datetime.fromisoformat(result)
    # Compare normalized to UTC since fromisoformat may return datetime.timezone.utc
    assert parsed.astimezone(_UTC).tzinfo == _UTC


def test_current_timestamp():
    """Test current_timestamp returns float."""
    result = IClock.current_timestamp()
    assert isinstance(result, float)
    assert result > 0


def test_resolve_timezone_with_zoneinfo():
    """Test resolve_timezone with ZoneInfo object."""
    result = IClock.resolve_timezone(_TOKYO)
    assert result == _TOKYO


def test_resolve_timezone_with_string():
    """Test resolve_timezone with timezone string."""
    result = IClock.resolve_timezone("America/New_York")
    assert result == _NY


def test_resolve_timezone_with_empty_string():
    """Test resolve_timezone with empty string returns UTC."""
    result = IClock.resolve_timezone("")
    assert result == _UTC


def test_resolve_timezone_with_none():
    """Test resolve_timezone with None returns UTC."""
    result = IClock.resolve_timezone(None)
    assert result == _UTC
