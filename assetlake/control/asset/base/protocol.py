from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from assetlake.control.access.base.protocol import IAccessLike
from assetlake.domain.asset.filesystem import AssetFilesystem
from assetlake.domain.asset.objectkind import AssetObjectkind


@runtime_checkable
class IAssetObjectLike(Protocol):
    uri: str
    size: int | None
    modified_at: datetime | None
    partitions: dict[str, str]

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> IAssetObjectLike: ...

    def describe(self) -> str: ...
    def export(self) -> dict[str, Any]: ...


@runtime_checkable
class IAssetLike(Protocol):
    glob: str
    name: str | None
    filesystem: AssetFilesystem
    objectkind: AssetObjectkind
    partitions: list[str] | None
    description: str | None
    owner: str | None
    metadata: dict[str, Any]
    tags: dict[str, str]

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> IAssetLike: ...

    def inspect(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
        access: IAccessLike | None = None,
    ) -> None: ...

    def export(self) -> dict[str, Any]: ...

    def describe(self) -> dict[str, Any]: ...
