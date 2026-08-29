from __future__ import annotations

from abc import ABC
from typing import ClassVar

from pydantic import Field

from assetlake.domain.compute.runtime import ComputeRuntime
from assetlake.internal.idomain import IDomain


class AbstractComputeDomain(
    IDomain,
    ABC,
):
    """
    Abstract base class for compute resources.

    Attributes:
        name (str): Name of the compute resource.
        runtime (ComputeRuntime): Runtime kind of the compute resource (e.g., local_py_entrypoint).
        tags (dict[str, str]): Tags associated with the compute resource.

    Methods:
        from_dict(value): Convert dict or instance to compute model (inherited).
        export(): Export the compute model as a dictionary.
        describe(): Export compute as JSON string (inherited).
        clone(**updates): Create a deep copy with updates (inherited).

    """

    _id_enabled: ClassVar[bool] = False
    name: str = Field(
        ...,
        description="Name of the compute resource",
    )
    runtime: ComputeRuntime = Field(
        ...,
        description="Runtime kind of the compute resource",
    )
    tags: dict[str, str] = Field(
        default_factory=dict,
        description="Tags associated with the compute resource",
    )
