from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fsspec.implementations.local import LocalFileSystem

from assetlake.control.access.local.local import LocalAccess
from assetlake.control.asset.base.factory import AssetFactory
from assetlake.control.asset.base.protocol import IAssetLike
from assetlake.control.asset.local.object import LocalAssetObject
from assetlake.domain.asset.asset import AbstractAssetDomain
from assetlake.domain.asset.filesystem import AssetFilesystem
from assetlake.domain.asset.objectkind import AssetObjectkind
from assetlake.internal.iclock import IClock
from assetlake.internal.idomainobject import IDomainObject


class LocalAssetDomain(AbstractAssetDomain):
    filesystem: AssetFilesystem = AssetFilesystem.LOCAL


@AssetFactory.add(AssetFilesystem.LOCAL)
class LocalAsset(
    IDomainObject,
    IAssetLike,
):
    _domain_class: type[LocalAssetDomain] = LocalAssetDomain

    def __init__(
        self,
        glob: str,
        name: str | None = None,
        objectkind: AssetObjectkind | None = None,
        partitions: list[str] | None = None,
        description: str | None = None,
        owner: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            glob=glob,
            name=name,
            objectkind=objectkind,
            partitions=partitions,
            description=description,
            owner=owner,
            metadata=metadata,
            tags=tags,
        )

    def get_mount(
        self,
        access: LocalAccess | None = None,
    ) -> LocalFileSystem:
        if access is not None:
            _opts = access.get_fsspec_opts()
            return LocalFileSystem(auto_mkdir=True, **_opts)
        else:
            return LocalFileSystem(auto_mkdir=True)

    def inspect(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
        access: LocalAccess | None = None,  # No ops
    ) -> list[LocalAssetObject]:
        """
        Inspect the local asset and return a list of local object references.

        Args:
            since (datetime | None): Optional start time for filtering objects.
            until (datetime | None): Optional end time for filtering objects.
            limit (int | None): Optional limit on the number of objects to return.
        """
        _results: list[LocalAssetObject] = []
        _mount = self.get_mount(access)
        for _item in _mount.glob(self.domain.glob):
            _item_info = _mount.info(_item)
            _modified_ts: float | None = _item_info.get("mtime", None)
            _modified_at: datetime | None = IClock.from_timestamp(_modified_ts)
            if since and _modified_at and _modified_at < since:
                continue
            if until and _modified_at and _modified_at > until:
                continue
            _type: str = _item_info["type"]
            _uri: str = _item_info["name"]
            _size: int | None = _item_info.get("size", None)
            _created_ts: float | None = _item_info.get("created", None)
            _created_at: datetime | None = IClock.from_timestamp(_created_ts)
            _metadata: dict[str, Any] = {
                "islink": _item_info.get("islink", None),
                "mode": _item_info.get("mode", None),
                "uid": _item_info.get("uid", None),
                "gid": _item_info.get("gid", None),
                "ino": _item_info.get("ino", None),
                "nlink": _item_info.get("nlink", None),
            }
            _obj: LocalAssetObject = LocalAssetObject(
                uri=_uri,
                size=_size,
                modified_at=_modified_at,
                metadata=_metadata,
                created_at=_created_at,
                type=_type,
            )
            _results.append(_obj)
            # Exit early if we have reached the limit
            if limit and len(_results) >= limit:
                break

        _min_datetime = datetime.min.replace(tzinfo=timezone.utc)
        _results.sort(key=lambda x: x.modified_at or _min_datetime, reverse=True)
        return _results
