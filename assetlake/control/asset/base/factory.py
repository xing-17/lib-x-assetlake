from __future__ import annotations

from typing import Any

from assetlake.control.asset.base.protocol import IAssetLike
from assetlake.domain.asset.asset import AbstractAssetDomain


class AssetFactory:
    """
    Factory for creating filesystem-specific asset instances.

    Attributes:
        _registry: filesystem-to-class mapping.

    Methods:
        add: Decorator to register asset class for platform.
        load: Create asset instance from data or domain model.
    """

    _registry: dict[str, type[IAssetLike]] = {}

    @classmethod
    def add(
        cls,
        filesystem: str,
    ) -> None:
        def decorator(klass: type[IAssetLike]):
            if filesystem in cls._registry:
                raise ValueError(f"'{filesystem}' asset already registered.")
            cls._registry[filesystem] = klass
            return klass

        return decorator

    @classmethod
    def load(
        cls,
        data: dict[str, Any] | AbstractAssetDomain,
    ) -> IAssetLike:
        # Determine the filesystem from the data or domain model
        if isinstance(data, AbstractAssetDomain):
            filesystem = getattr(data, "filesystem", None)
        else:
            filesystem = data.get("filesystem", None)

        if not filesystem:
            raise ValueError("Asset data missing required field: 'filesystem'")

        # Look up the registered class for the filesystem
        klass: type[IAssetLike] | None = cls._registry.get(filesystem)
        if klass is None:
            raise ValueError(f"No asset registered for '{filesystem}'")

        # Determine whether to load from dict or domain model
        if isinstance(data, AbstractAssetDomain):
            return klass.from_domain(data)
        else:
            return klass.from_dict(data)
