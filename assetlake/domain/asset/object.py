from __future__ import annotations

from abc import ABC
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from pydantic import Field, field_validator, model_validator

from assetlake.domain.asset.objectkind import AssetObjectkind
from assetlake.internal.iclock import IClock
from assetlake.internal.idomain import IDomain


class AbstractAssetObjectDomain(
    IDomain,
    ABC,
):
    """
    Abstract base class for logical data assets across platforms.

    Attributes:
        uri (str): Physical URI of the asset component (e.g., 's3://bucket/path/file.parquet').
        size (int | None): Size of the asset reference in bytes
        modified_at (datetime | None): Last modified timestamp of this asset component.
        partitions (dict[str, str]): Partition information for this asset component.
        metadata (dict[str, Any]): Additional metadata associated with the asset reference.

    Methods:
        from_dict(dict data): Create instance from dictionary data.
        export(): Export the underlying domain model to a dictionary.
        describe(): Return a JSON string representation of the domain model.
        clone(**updates): Create a deep copy with updates (inherited).

    """

    _id_enabled: ClassVar[bool] = False
    uri: str = Field(
        ...,
        description="Physical URI of the asset component (e.g., 's3://bucket/path/file.parquet').",
    )
    objectkind: AssetObjectkind = Field(
        default=AssetObjectkind.OBJECT,
        description="Kind of the asset component, default: OBJECT.",
    )
    size: int | None = Field(
        default=None,
        description="Size of the asset reference in bytes",
    )
    modified_at: datetime | None = Field(
        default=None,
        description="Last modified timestamp of this asset component.",
    )
    partitions: dict[str, str] = Field(
        default_factory=dict,
        description="Partition information for this asset component.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata associated with the asset reference.",
    )

    @field_validator("modified_at", mode="before")
    @classmethod
    def _coerce_optional_datetime(cls, v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, str):
            return IClock.from_iso(v)
        if isinstance(v, datetime):
            return IClock.from_datetime(v)
        return v

    @model_validator(mode="before")
    @classmethod
    def _infer_from_uri(
        cls,
        data: Any,
    ) -> Any:
        if not isinstance(data, dict):
            return data
        _uri = data.get("uri", "")
        if "partitions" not in data or data["partitions"] is None:
            data["partitions"] = _infer_partitions(_uri)
        if "suffix" not in data or data["suffix"] is None:
            data["suffix"] = _infer_suffix(_uri)
        if "objectkind" not in data or data["objectkind"] is None:
            data["objectkind"] = _infer_objectkind(_uri)
        return data


def _infer_objectkind(glob: str) -> AssetObjectkind:
    if glob.endswith(".parquet"):
        return AssetObjectkind.PARQUET
    elif glob.endswith(".csv"):
        return AssetObjectkind.CSV
    else:
        return AssetObjectkind.OBJECT


def _infer_suffix(uri: str) -> str | None:
    try:
        path = Path(uri).expanduser().resolve()
        return path.suffix if path.suffix else None
    except Exception:
        return None


def _infer_partitions(uri: str) -> dict[str, str]:
    try:
        path = Path(uri).expanduser().resolve()
        partitions: dict[str, str] = {}
        for part in path.parts:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            partitions[key] = value
        return partitions
    except Exception:
        return {}
