from __future__ import annotations

from assetlake.domain.asset.filesystem import AssetFilesystem
from assetlake.domain.asset.object import AbstractAssetObjectDomain


class S3AssetObject(AbstractAssetObjectDomain):
    """
    An S3 object.

    Attributes:
        uri: (str) S3 URI of the object (e.g., s3://bucket/path/to/object)
        filesystem: Fixed to AssetFilesystem.S3.
        objectkind: Kind of the object, default: OBJECT
        size: Size of the object in bytes
        modified_at: Last modified timestamp of the object
        partitions: Partition values extracted from the S3 key path (if applicable)

    """

    filesystem: AssetFilesystem = AssetFilesystem.S3
    storage_class: str | None = None
    etag: str | None = None
