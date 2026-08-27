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
        uri: (str) Local file URI of the object (e.g., /path/to/object)
        filesystem (AssetFilesystem): Fixed to AssetFilesystem.LOCAL
        objectkind (AssetObjectkind): Kind of the object, default: OBJECT
        size (int | None): Size of the object in bytes
        modified_at (datetime | None): Last modified timestamp of the object
        partitions (dict[str, str] | None): Partition values extracted from the local file path
        path (Path): Computed property that returns the Path object corresponding to the URI.

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
