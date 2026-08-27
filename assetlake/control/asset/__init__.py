from __future__ import annotations

from assetlake.control.asset import (
    local,  # NoQA: F401
    oss,  # NoQA: F401
    s3,  # NoQA: F401
)
from assetlake.control.asset.local import (
    LocalAsset,
    LocalAssetDomain,
    LocalAssetObject,
)
from assetlake.control.asset.oss import (
    OSSAsset,
    OSSAssetDomain,
    OSSAssetObject,
)
from assetlake.control.asset.s3 import (
    S3Asset,
    S3AssetDomain,
    S3AssetObject,
)

__all__ = [
    "LocalAsset",
    "LocalAssetDomain",
    "LocalAssetObject",
    "OSSAsset",
    "OSSAssetDomain",
    "OSSAssetObject",
    "S3Asset",
    "S3AssetDomain",
    "S3AssetObject",
]
