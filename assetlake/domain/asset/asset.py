from __future__ import annotations

from abc import ABC
from typing import Any, ClassVar
from urllib.parse import urlparse

from pydantic import Field, model_validator

from assetlake.domain.asset.filesystem import AssetFilesystem
from assetlake.domain.asset.objectkind import AssetObjectkind
from assetlake.internal.idomain import IDomain


class AbstractAssetDomain(
    IDomain,
    ABC,
):
    """
    Abstract base class for logical data asset objects across platforms.

    Attributes:
        glob (str): Glob pattern for the asset (e.g., 's3://bucket/path/*.parquet').
        name (str): Name of the asset.
        objectkind (AssetObjectkind): Kind of the asset, default: OBJECT.
        filesystem (AssetFilesystem): File system of the asset, default: LOCAL.
        partitions (list[str]): List of partition keys: default: empty list.
        description (str | None): Optional description of the asset.
        owner (str | None): Optional owner of the asset.
        metadata (dict[str, Any]): Additional metadata associated with the asset.
        tags (dict[str, str]): Tags associated with the asset.

    Methods:
        from_dict(dict data): Create instance from dictionary data.
        export(): Export the underlying domain model to a dictionary.
        describe(): Return a JSON string representation of the domain model.
        clone(**updates): Create a deep copy with updates (inherited).

    """

    _id_enabled: ClassVar[bool] = False
    glob: str = Field(
        ...,
        description="Glob pattern for the asset (e.g., 's3://bucket/path/*.parquet').",
    )
    name: str | None = Field(
        default=None,
        description="Name of the asset",
    )
    filesystem: AssetFilesystem = Field(
        AssetFilesystem.LOCAL,
        description="File system of the asset",
    )
    objectkind: AssetObjectkind = Field(
        AssetObjectkind.OBJECT,
        description="Kind of the asset",
    )
    partitions: list[str] = Field(
        default_factory=list,
        description="Partition keys for the asset",
    )
    description: str | None = Field(
        default=None,
        description="Optional description of the asset",
    )
    owner: str | None = Field(
        default=None,
        description="Owner of the asset",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata associated with the asset",
    )
    tags: dict[str, str] = Field(
        default_factory=dict,
        description="Tags associated with the asset",
    )

    @model_validator(mode="before")
    @classmethod
    def _infer_from_glob(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        _glob = data.get("glob", "")
        if "objectkind" not in data:
            data["objectkind"] = _infer_objectkind(_glob)
        if "partitions" not in data:
            data["partitions"] = _infer_partitions(_glob)
        return data


def _infer_objectkind(glob: str) -> AssetObjectkind:
    if glob.endswith(".parquet"):
        return AssetObjectkind.PARQUET
    elif glob.endswith(".csv"):
        return AssetObjectkind.CSV
    else:
        return AssetObjectkind.OBJECT


def _infer_partitions(glob: str) -> list[str]:
    try:
        parsed = urlparse(glob)
        path = parsed.path if parsed.scheme else glob
        partitions = []
        for segment in path.split("/"):
            if not segment:
                continue
            if "=" in segment:
                key, _ = segment.split("=", 1)
                partitions.append(key)
        return partitions
    except Exception:
        return []
