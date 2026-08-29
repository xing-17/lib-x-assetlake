from __future__ import annotations

from assetlake.control.access import (
    aliyun,  # NoQA: F401
    aws,  # NoQA: F401
    local,  # NoQA: F401
)
from assetlake.control.access.aliyun import (
    AliyunAccess,
    AliyunAccessDomain,
)
from assetlake.control.access.aws import (
    AWSAccess,
    AWSAccessDomain,
)
from assetlake.control.access.base.factory import AccessFactory
from assetlake.control.access.base.protocol import IAccessLike
from assetlake.control.access.local import (
    LocalAccess,
    LocalAccessDomain,
)

__all__ = [
    "LocalAccess",
    "LocalAccessDomain",
    "AliyunAccess",
    "AliyunAccessDomain",
    "AWSAccess",
    "AWSAccessDomain",
    "AccessFactory",
    "IAccessLike",
]
