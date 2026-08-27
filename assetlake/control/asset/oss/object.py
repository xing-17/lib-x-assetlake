from __future__ import annotations

from assetlake.domain.asset.filesystem import AssetFilesystem
from assetlake.domain.asset.object import AbstractAssetObjectDomain


class OSSAssetObject(AbstractAssetObjectDomain):
    """
    An OSS object.

    Attributes:
        uri: (str) OSS URI of the object (e.g., oss://bucket/path/to/object)
        filesystem: Fixed to AssetFilesystem.
        objectkind: Kind of the object, default: OBJECT
        size: Size of the object in bytes
        modified_at: Last modified timestamp of the object
        partitions: Partition values extracted from the local file path (if applicable)

    """

    filesystem: AssetFilesystem = AssetFilesystem.OSS
