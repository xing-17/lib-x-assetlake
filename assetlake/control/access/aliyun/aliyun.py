from __future__ import annotations

from duckdb import DuckDBPyConnection

from assetlake.control.access.base.factory import AccessFactory
from assetlake.control.access.base.protocol import IAccessLike
from assetlake.domain.access.access import AbstractAccessDomain
from assetlake.domain.access.platform import AccessPlatform
from assetlake.internal.idomainobject import IDomainObject


class AliyunAccessDomain(AbstractAccessDomain):
    """
    阿里云 Access Domain class for managing Alibaba Cloud credentials.

    source: https://www.alibabacloud.com/help/zh/sdk/developer-reference/v2-manage-python-access-credentials

    Attributes:
        name: Name of the access profile.
        platform: AccessPlatform fixed to ALIYUN.
        access_key_id: 阿里云访问密钥ID。
        access_key_secret: 阿里云访问密钥Secret。
        region: 阿里云区域。
        internal: 是否使用内网访问阿里云服务。
        tags: 与访问配置文件关联的标签字典。

    """

    platform: AccessPlatform = AccessPlatform.ALIYUN
    access_key_id: str | None = None
    access_key_secret: str | None = None


@AccessFactory.add(AccessPlatform.ALIYUN)
class AliyunAccess(
    IDomainObject,
    IAccessLike,
):
    """
    Aliyun access control wrapper for managing Alibaba Cloud credentials.

    Attributes:
        name: Name of the access profile.
        platform: AccessPlatform fixed to ALIYUN.
        access_key_id: 阿里云访问密钥ID。
        access_key_secret: 阿里云访问密钥Secret。
        region: 阿里云区域。
        internal: 是否使用内网访问阿里云服务。
        tags: 与访问配置文件关联的标签字典。

    """

    _domain_class = AliyunAccessDomain

    def __init__(
        self,
        name: str | None = None,
        access_key_id: str | None = None,
        access_key_secret: str | None = None,
        tags: dict[str, str] = None,
    ):
        super().__init__(
            name=name,
            platform=AccessPlatform.ALIYUN,
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            tags=tags,
        )

    def get_fsspec_opts(self) -> dict[str, str | None]:
        _payload = {
            "access_key_id": self.access_key_id,
            "access_key_secret": self.access_key_secret,
        }
        return {k: v for k, v in _payload.items() if v is not None}

    def to_duckdb(
        self,
        conn: DuckDBPyConnection,
        region: str | None = None,
        endpoint: str | None = None,
    ) -> DuckDBPyConnection:
        _key_id = self.access_key_id
        _secret = self.access_key_secret
        if not _key_id or not _secret:
            return conn
        else:
            _name = self.name or "aliyun_access"
            _config = {
                "TYPE": "s3",
                "PROVIDER": "config",
                "KEY_ID": _key_id,
                "SECRET": _secret,
                "REGION": region,
                "ENDPOINT": endpoint,
                "URL_STYLE": "vhost",
            }
            _config = {k: v for k, v in _config.items() if v is not None}
            _sql = f"CREATE OR REPLACE SECRET {_name} ("
            _sql += ", ".join([f"{k} '{v}'" for k, v in _config.items()])
            _sql += ");"
            conn.execute(_sql)
            return conn

    def export(self) -> dict[str, str | None]:
        _key_id = self.access_key_id
        _expr_key_id = None if not _key_id else _key_id[0:4] + "******"
        _secret = self.access_key_secret
        _expr_secret = None if not _secret else _secret[0:4] + "******"
        return {
            "name": self.name,
            "platform": self.platform.value,
            "access_key_id": _expr_key_id,
            "access_key_secret": _expr_secret,
            "tags": self.tags,
        }
