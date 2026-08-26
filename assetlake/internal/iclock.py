from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

_UTC_TIMEZONE: ZoneInfo = ZoneInfo("UTC")


class IClock:
    """
    Provides UTC clock utilities for timezone-aware datetime operations.

    Methods:
        from_iso(value: str): Convert an ISO 8601 string to a timezone-aware datetime.
        from_timestamp(value: float): Convert a POSIX timestamp to a timezone-aware datetime.
        current(): Return the current datetime (timezone-aware).
        current_iso(): Return the current time as an ISO 8601 string.
        current_timestamp(): Return the current time as a POSIX timestamp.

    """

    def __init__(self):
        raise TypeError("IClock is not intended to be instantiated")

    @staticmethod
    def resolve_timezone(
        timezone: ZoneInfo | str | None = None,
    ) -> ZoneInfo:
        if isinstance(timezone, ZoneInfo):
            return timezone
        elif isinstance(timezone, str):
            return ZoneInfo(timezone) if timezone else _UTC_TIMEZONE
        else:
            return _UTC_TIMEZONE

    @staticmethod
    def from_datetime(value: datetime) -> datetime:
        if value.tzinfo:
            return value.astimezone(_UTC_TIMEZONE)
        else:
            return value.replace(tzinfo=_UTC_TIMEZONE)

    @staticmethod
    def from_iso(value: str) -> datetime | None:
        if not value:
            return None
        _dt = datetime.fromisoformat(value)
        if _dt.tzinfo:
            return _dt.astimezone(_UTC_TIMEZONE)
        else:
            return _dt.replace(tzinfo=_UTC_TIMEZONE)

    @staticmethod
    def from_timestamp(value: float) -> datetime:
        return datetime.fromtimestamp(value, tz=_UTC_TIMEZONE)

    @staticmethod
    def current() -> datetime:
        return datetime.now(tz=_UTC_TIMEZONE)

    @staticmethod
    def current_iso() -> str:
        return IClock.current().isoformat()

    @staticmethod
    def current_timestamp() -> float:
        return IClock.current().timestamp()
