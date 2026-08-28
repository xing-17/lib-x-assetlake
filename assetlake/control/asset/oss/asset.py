from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import duckdb
from duckdb import DuckDBPyConnection
from pydantic import Field, computed_field

from assetlake.control.access.aliyun.aliyun import AliyunAccess
from assetlake.control.asset.base.factory import AssetFactory
from assetlake.control.asset.base.protocol import IAssetLike
from assetlake.control.asset.oss.object import OSSAssetObject
from assetlake.domain.asset.asset import AbstractAssetDomain
from assetlake.domain.asset.filesystem import AssetFilesystem
from assetlake.domain.asset.objectkind import AssetObjectkind
from assetlake.internal.iclock import IClock
from assetlake.internal.idomainobject import IDomainObject
from assetlake.internal.iglob import IGlob


class OSSAssetDomain(AbstractAssetDomain):
    filesystem: AssetFilesystem = AssetFilesystem.OSS
    region: str = Field(
        ...,
        description="The region of the OSS bucket",
    )
    internal: bool = Field(
        default=False,
        description="Whether to use the internal endpoint for OSS",
    )

    @computed_field
    @property
    def bucket(self) -> str | None:
        return IGlob.parse_bucket(self.glob)

    @computed_field
    @property
    def common_prefix(self) -> str | None:
        return IGlob.parse_common_prefix(self.glob)

    @computed_field
    @property
    def object_pattern(self) -> str | None:
        return IGlob.parse_object_pattern(self.glob)

    @computed_field
    @property
    def endpoint(self) -> str:
        if self.internal:
            return f"oss-{self.region}-internal.aliyuncs.com"
        else:
            return f"oss-{self.region}.aliyuncs.com"


@AssetFactory.add(AssetFilesystem.OSS)
class OSSAsset(
    IDomainObject,
    IAssetLike,
):
    _domain_class: type[OSSAssetDomain] = OSSAssetDomain
    _extra_duckdb_modules: list[str] = ["httpfs", "s3"]

    def __init__(
        self,
        glob: str,
        region: str,
        name: str | None = None,
        objectkind: AssetObjectkind | None = None,
        partitions: list[str] | None = None,
        description: str | None = None,
        owner: str | None = None,
        metadata: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            glob=glob,
            region=region,
            name=name,
            objectkind=objectkind,
            partitions=partitions,
            description=description,
            owner=owner,
            metadata=metadata,
            tags=tags,
        )

    def _get_client(
        self,
        access: AliyunAccess | None = None,
    ) -> Any:
        try:
            from alibabacloud_oss_v2 import Client, config
            from alibabacloud_oss_v2.credentials import (
                EnvironmentVariableCredentialsProvider,
                StaticCredentialsProvider,
            )

            if access:
                pvd = StaticCredentialsProvider(
                    access_key_id=access.access_key_id,
                    access_key_secret=access.access_key_secret,
                )
            else:
                pvd = EnvironmentVariableCredentialsProvider()
            cfg = config.load_default()
            cfg.region = self.domain.region
            cfg.endpoint = self.domain.endpoint
            cfg.credentials_provider = pvd
            return Client(cfg)
        except ImportError as e:
            raise ImportError("alibabacloud-oss-v2 is required for OSSAsset.") from e
        except Exception as e:
            raise RuntimeError(f"Failed to create OSS client: {e}") from e

    def _get_iterator(
        self,
        access: AliyunAccess | None = None,
    ) -> Any:
        _client = self._get_client(access)
        try:
            import alibabacloud_oss_v2 as oss

            paginator = _client.list_objects_v2_paginator()
            request = oss.ListObjectsV2Request(
                bucket=self.domain.bucket,
                prefix=self.domain.common_prefix,
            )
            return paginator.iter_page(request)
        except Exception as e:
            raise RuntimeError(f"Failed to get OSS object iterator: {e}") from e

    def _get_duckdb_conn(
        self,
        access: AliyunAccess | None = None,
    ) -> DuckDBPyConnection:
        conn = duckdb.connect(database=":memory:")
        for module in self._extra_duckdb_modules:
            conn.execute(f"INSTALL {module};")
            conn.execute(f"LOAD {module};")
        access = access or AliyunAccess()
        conn = access.to_duckdb(
            conn=conn,
            region=self.domain.region,
            endpoint=self.domain.endpoint,
        )
        return conn

    def inspect(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
        access: AliyunAccess | None = None,  # No ops
    ) -> list[OSSAssetObject]:
        """
        Inspect the local asset and return a list of local object references.

        Args:
            since (datetime | None): Optional start time for filtering objects.
            until (datetime | None): Optional end time for filtering objects.
            limit (int | None): Optional limit on the number of objects to return.
            access (AliyunAccess | None): Optional access credentials for OSS.
        """
        _results: list[OSSAssetObject] = []
        _continue: bool = True
        for page in self._get_iterator(access):
            for obj in page.contents:
                _modified_at: datetime | None = IClock.from_datetime(obj.last_modified)
                if since and _modified_at and _modified_at < since:
                    continue
                if until and _modified_at and _modified_at > until:
                    continue
                _key: str = obj.key
                _uri: str = f"oss://{self.domain.bucket}/{_key}"
                if not IGlob.match(self.domain.glob, _uri):
                    continue
                _size: int | None = obj.size
                _obj: OSSAssetObject = OSSAssetObject(
                    uri=_uri,
                    size=_size,
                    modified_at=_modified_at,
                )
                _results.append(_obj)

                # Exit early if we have reached the limit
                if limit and len(_results) >= limit:
                    _continue = False
                    break

            # Exit the outer loop if we have reached the limit
            if not _continue:
                break

        _min_datetime = datetime.min.replace(tzinfo=timezone.utc)
        _results.sort(key=lambda x: x.modified_at or _min_datetime, reverse=True)
        return _results

    def quality(
        self,
        conn: DuckDBPyConnection | None = None,
        access: AliyunAccess | None = None,
        objects: list[OSSAssetObject] | None = None,
    ) -> list[dict[str, Any]]:
        if self.domain.objectkind != AssetObjectkind.PARQUET:
            raise ValueError("Quality check is only supported for PARQUET")

        # Ensure duckdb connection
        conn = conn or self._get_duckdb_conn(access=access)

        # Build query
        if not objects:
            _glob = self.domain.glob
            if not _glob.startswith("oss://"):
                _glob = _glob.replace("oss://", "s3://")
            _param = (_glob,)
        else:
            _uris = []
            for obj in objects:
                _uri = obj.uri
                if _uri.startswith("oss://"):
                    _uri = _uri.replace("oss://", "s3://")
                _uris.append(_uri)
            _param = (_uris,)

        # Run quality check
        _stmt = "SELECT * FROM parquet_metadata(?);"
        _cursor = conn.execute(_stmt, _param)
        _columns = [desc[0] for desc in _cursor.description]
        _rows = _cursor.fetchall()
        _results = [dict(zip(_columns, row)) for row in _rows]
        return _results
