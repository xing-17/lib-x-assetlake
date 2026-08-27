from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import computed_field

from assetlake.domain.asset.filesystem import AssetFilesystem
from assetlake.domain.asset.object import AbstractAssetObjectDomain


class LocalAssetObject(AbstractAssetObjectDomain):
    """
    A local file system object.

    Attributes:
        uri: (str) Local file URI of the object (e.g., file:///path/to/object)
        filesystem: Fixed to AssetFilesystem.LOCAL
        objectkind: Kind of the object, default: OBJECT
        size: Size of the object in bytes
        modified_at: Last modified timestamp of the object
        partitions: Partition values extracted from the local file path (if applicable)

    """
    filesystem: AssetFilesystem = AssetFilesystem.LOCAL
    type: str | None = None
    created_at: datetime | None = None

    @computed_field
    @property
    def path(self) -> Path:
        _uri = self.uri
        if "file://" in self.uri:
            _uri = _uri.replace("file://", "")
        return Path(_uri).expanduser().resolve()
