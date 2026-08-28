from __future__ import annotations

from duckdb import DuckDBPyConnection

from assetlake.control.access.base.factory import AccessFactory
from assetlake.control.access.base.protocol import IAccessLike
from assetlake.domain.access.access import AbstractAccessDomain
from assetlake.domain.access.platform import AccessPlatform
from assetlake.internal.idomainobject import IDomainObject


class AWSAccessDomain(AbstractAccessDomain):
    """
    AWS Access Domain class for managing credentials.

    source: https://docs.aws.amazon.com/boto3/latest/reference/core/session.html

    Attributes:
        name: Name of the access profile.
        platform: AccessPlatform fixed to AWS.
        access_key_id: AWS access key ID.
        access_key_secret: AWS secret access key.
        session_token: AWS session token for temporary credentials.
        profile: AWS CLI profile name.
        region: AWS region name.
        account: AWS account ID.
        tags: Dictionary of tags associated with the access profile.

    """

    platform: AccessPlatform = AccessPlatform.AWS
    access_key_id: str | None = None
    access_key_secret: str | None = None
    session_token: str | None = None
    profile: str | None = None
    region: str | None = None
    account: str | None = None


@AccessFactory.add(AccessPlatform.AWS)
class AWSAccess(
    IDomainObject,
    IAccessLike,
):
    """
    AWS access control wrapper for managing AWS credentials.

    Attributes:
        name: Name of the access profile.
        platform: AccessPlatform fixed to AWS.
        access_key_id: AWS access key ID.
        access_key_secret: AWS secret access key.
        session_token: AWS session token for temporary credentials.
        profile: AWS CLI profile name.
        region: AWS region name.
        account: AWS account ID.
        tags: Tags associated with the access profile.

    """

    _domain_class = AWSAccessDomain

    def __init__(
        self,
        name: str | None = None,
        access_key_id: str | None = None,
        access_key_secret: str | None = None,
        session_token: str | None = None,
        profile: str | None = None,
        region: str | None = None,
        account: str | None = None,
        tags: dict[str, str] = None,
    ):
        super().__init__(
            name=name,
            platform=AccessPlatform.AWS,
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            session_token=session_token,
            profile=profile,
            region=region,
            account=account,
            tags=tags,
        )

    def get_fsspec_opts(self) -> dict[str, str | None]:
        _opts = {
            "key": self.access_key_id,
            "secret": self.access_key_secret,
            "profile": self.profile,
        }
        _filtered = {k: v for k, v in _opts.items() if v is not None}
        return _filtered

    def to_duckdb(
        self,
        conn: DuckDBPyConnection,
    ) -> DuckDBPyConnection:
        _key_id = self.access_key_id
        _secret = self.access_key_secret
        if not _key_id or not _secret:
            return conn
        else:
            _name = self.name or "aws_access"
            _config = {
                "TYPE": "s3",
                "PROVIDER": "config",
                "KEY_ID": _key_id,
                "SECRET": _secret,
            }
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
        _token = self.session_token
        _expr_token = None if not _token else _token[0:4] + "******"
        return {
            "name": self.name,
            "platform": self.platform.value,
            "access_key_id": _expr_key_id,
            "access_key_secret": _expr_secret,
            "session_token": _expr_token,
            "profile": self.profile,
            "region": self.region,
            "account": self.account,
            "tags": self.tags,
        }
