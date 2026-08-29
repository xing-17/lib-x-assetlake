from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from duckdb import DuckDBPyConnection

from assetlake.domain.access.access import AbstractAccessDomain
from assetlake.domain.access.platform import AccessPlatform


@runtime_checkable
class IAccessLike(Protocol):
    name: str
    platform: AccessPlatform
    tags: dict[str, str]

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> IAccessLike: ...

    @classmethod
    def from_domain(
        cls,
        domain: AbstractAccessDomain,
    ) -> IAccessLike: ...

    def get_fsspec_opts(self) -> dict[str, str | None]: ...

    def to_duckdb(
        self,
        conn: DuckDBPyConnection,
        **kwargs: Any,
    ) -> DuckDBPyConnection: ...

    def export(self) -> dict[str, Any]: ...
    def describe(self) -> str: ...
