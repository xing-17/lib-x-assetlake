from __future__ import annotations

from enum import StrEnum


class AssetFilesystem(StrEnum):
    """
    Enumeration of supported storage platforms for assets.

    Values:
        LOCAL: Local file system storage.
        S3: AWS S3 cloud storage.
        OSS: Alibaba Cloud OOS.

    """

    LOCAL = "local"
    S3 = "s3"
    OSS = "oss"
