from __future__ import annotations

from duckdb import DuckDBPyConnection

from assetlake.control.access.base.factory import AccessFactory
from assetlake.control.access.base.protocol import IAccessLike
from assetlake.domain.access.access import AbstractAccessDomain
from assetlake.domain.access.platform import AccessPlatform
from assetlake.internal.idomainobject import IDomainObject


class LocalAccessDomain(AbstractAccessDomain):
    """
    Local Access Domain class for managing credentials.

    No Ops class, for granularity only.

    Attributes:
        name: Name of the access profile.
        platform: AccessPlatform fixed to LOCAL.
        tags: Dictionary of tags associated with the access profile.

    """

    platform: AccessPlatform = AccessPlatform.LOCAL


@AccessFactory.add(AccessPlatform.LOCAL)
class LocalAccess(
    IDomainObject,
    IAccessLike,
):
    """
    Local access control wrapper. No-op credentials for local platform.

    Attributes:
        name: Name of the access profile.
        platform: AccessPlatform fixed to LOCAL.
        tags: Tags associated with the access profile.

    """

    _domain_class = LocalAccessDomain

    def __init__(
        self,
        name: str | None = None,
        tags: dict[str, str] = None,
    ):
        super().__init__(
            name=name,
            platform=AccessPlatform.LOCAL,
            tags=tags,
        )

    def get_fsspec_opts(self) -> dict[str, str | None]:
        # No ops for local access
        return {}

    def to_duckdb(
        self,
        conn: DuckDBPyConnection,
    ) -> DuckDBPyConnection:
        # No ops for local access
        return conn

    def export(self) -> dict[str, str | None]:
        return {
            "name": self.name,
            "platform": self.platform.value,
            "tags": self.tags,
        }
