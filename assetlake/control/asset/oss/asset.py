from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

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
