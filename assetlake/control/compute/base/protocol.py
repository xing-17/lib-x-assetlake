from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from assetlake.control.access.base.protocol import IAccessLike
from assetlake.domain.compute.compute import AbstractComputeDomain
from assetlake.domain.compute.runtime import ComputeRuntime


@runtime_checkable
class IComputeLike(Protocol):
    name: str
    runtime: ComputeRuntime
    tags: dict[str, str]

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> IComputeLike: ...

    @classmethod
    def from_domain(
        cls,
        domain: AbstractComputeDomain,
    ) -> IComputeLike: ...

    def inspect(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
        access: IAccessLike | None = None,
    ) -> list[dict[str, Any]]: ...

    def export(self) -> dict[str, Any]: ...
    def describe(self) -> str: ...
