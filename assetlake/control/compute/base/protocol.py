from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from assetlake.control.access.base.protocol import IAccessLike
from assetlake.domain.compute.compute import AbstractComputeDomain
from assetlake.domain.compute.runtime import ComputeRuntime


@runtime_checkable
class ISubmitHandleLike(Protocol):
    def collect(self) -> dict[str, Any]: ...


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

    def execute(
        self,
        params: dict[str, Any] | None = None,
        access: IAccessLike | None = None,
    ) -> dict[str, Any]: ...

    def submit(
        self,
        params: dict[str, Any] | None = None,
        access: IAccessLike | None = None,
    ) -> ISubmitHandleLike: ...

    def inspect(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
        access: IAccessLike | None = None,
    ) -> list[dict[str, Any]]: ...

    def export(self) -> dict[str, Any]: ...
    def describe(self) -> str: ...
