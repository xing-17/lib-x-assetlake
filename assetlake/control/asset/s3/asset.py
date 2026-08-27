from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import Field, computed_field

from assetlake.control.access.aws.aws import AWSAccess
from assetlake.control.asset.base.factory import AssetFactory
from assetlake.control.asset.base.protocol import IAssetLike
from assetlake.control.asset.s3.object import S3AssetObject
from assetlake.domain.asset.asset import AbstractAssetDomain
from assetlake.domain.asset.filesystem import AssetFilesystem
from assetlake.domain.asset.objectkind import AssetObjectkind
from assetlake.internal.iclock import IClock
from assetlake.internal.idomainobject import IDomainObject
from assetlake.internal.iglob import IGlob


class S3AssetDomain(AbstractAssetDomain):
    filesystem: AssetFilesystem = AssetFilesystem.S3
    region: str | None = Field(
        default=None,
        description="The AWS region of the S3 bucket",
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


@AssetFactory.add(AssetFilesystem.S3)
class S3Asset(
    IDomainObject,
    IAssetLike,
):
    _domain_class: type[S3AssetDomain] = S3AssetDomain

    def __init__(
        self,
        glob: str,
        region: str | None = None,
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
        access: AWSAccess | None = None,
    ) -> Any:
        try:
            import boto3

            if access:
                session = boto3.Session(
                    aws_access_key_id=access.access_key_id,
                    aws_secret_access_key=access.access_key_secret,
                    aws_session_token=access.session_token,
                    profile_name=access.profile,
                    region_name=access.region or self.domain.region,
                )
            else:
                session = boto3.Session()
            return session.client("s3")
        except ImportError as e:
            raise ImportError("boto3 is required for S3Asset.") from e
        except Exception as e:
            raise RuntimeError(f"Failed to create S3 client: {e}") from e

    def _get_iterator(
        self,
        access: AWSAccess | None = None,
    ) -> Any:
        _client = self._get_client(access)
        try:
            paginator = _client.get_paginator("list_objects_v2")
            pages = paginator.paginate(
                Bucket=self.domain.bucket,
                Prefix=self.domain.common_prefix or "",
            )
            return pages
        except Exception as e:
            raise RuntimeError(f"Failed to get S3 object iterator: {e}") from e

    def inspect(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
        access: AWSAccess | None = None,
    ) -> list[S3AssetObject]:
        """
        Inspect the S3 asset and return a list of S3 object references.

        Args:
            since (datetime | None): Optional start time for filtering objects.
            until (datetime | None): Optional end time for filtering objects.
            limit (int | None): Optional limit on the number of objects to return.
            access (AWSAccess | None): Optional access credentials for AWS.
        """
        _results: list[S3AssetObject] = []
        _continue: bool = True
        for page in self._get_iterator(access):
            for obj in page.get("Contents", []):
                _modified_at: datetime | None = IClock.from_datetime(obj["LastModified"])
                if since and _modified_at and _modified_at < since:
                    continue
                if until and _modified_at and _modified_at > until:
                    continue
                _key: str = obj["Key"]
                _uri: str = f"s3://{self.domain.bucket}/{_key}"
                if not IGlob.match(self.domain.glob, _uri):
                    continue
                _size: int | None = obj.get("Size")
                _etag: str | None = obj.get("ETag")
                _storage_class: str | None = obj.get("StorageClass")
                _obj: S3AssetObject = S3AssetObject(
                    uri=_uri,
                    size=_size,
                    modified_at=_modified_at,
                    etag=_etag,
                    storage_class=_storage_class,
                    metadata=obj,
                )
                _results.append(_obj)

                if limit and len(_results) >= limit:
                    _continue = False
                    break

            if not _continue:
                break

        _min_datetime = datetime.min.replace(tzinfo=timezone.utc)
        _results.sort(key=lambda x: x.modified_at or _min_datetime, reverse=True)
        return _results
