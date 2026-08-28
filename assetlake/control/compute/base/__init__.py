"""Base compute module providing protocols and factory for compute instances."""

from assetlake.control.compute.base.factory import ComputeFactory
from assetlake.control.compute.base.protocol import IComputeLike, ISubmitHandleLike

__all__ = [
    "ComputeFactory",
    "IComputeLike",
    "ISubmitHandleLike",
]
