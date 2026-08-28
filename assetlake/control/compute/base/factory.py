from __future__ import annotations

from typing import Any

from assetlake.control.compute.base.protocol import IComputeLike
from assetlake.domain.compute.compute import AbstractComputeDomain


class ComputeFactory:
    """
    Factory for creating runtime-specific compute instances.

    Attributes:
        _registry: Runtime-to-class mapping.

    Methods:
        add: Decorator to register compute class for runtime.
        load: Create compute instance from data or domain model.
    """

    _registry: dict[str, type[IComputeLike]] = {}

    @classmethod
    def add(
        cls,
        runtime: str,
    ) -> None:
        def decorator(klass: type[IComputeLike]):
            if runtime in cls._registry:
                raise ValueError(f"'{runtime}' compute already registered.")
            cls._registry[runtime] = klass
            return klass

        return decorator

    @classmethod
    def load(
        cls,
        data: dict[str, Any] | AbstractComputeDomain,
    ) -> IComputeLike:
        # Determine the runtime from the data or domain model
        if isinstance(data, AbstractComputeDomain):
            runtime = getattr(data, "runtime", None)
        else:
            runtime = data.get("runtime", None)

        if not runtime:
            raise ValueError("Compute data missing required field: 'runtime'")

        # Look up the registered class for the platform
        klass: type[IComputeLike] | None = cls._registry.get(runtime)
        if klass is None:
            raise ValueError(f"No compute registered for '{runtime}'")

        # Determine whether to load from dict or domain model
        if isinstance(data, AbstractComputeDomain):
            return klass.from_domain(data)
        else:
            return klass.from_dict(data)
