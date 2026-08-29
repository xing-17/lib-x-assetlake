"""Compute control module providing compute implementations."""

from assetlake.control.compute.base.factory import ComputeFactory
from assetlake.control.compute.base.protocol import IComputeLike

# Import compute implementations to trigger factory registration
from assetlake.control.compute.glue import (
    GlueJobCompute,
    GlueJobComputeDomain,
)
from assetlake.control.compute.py_entrypoint import (
    PyEntrypointCompute,
    PyEntrypointComputeDomain,
    PyEntrypointHandle,
)
from assetlake.control.compute.stepfunction import (
    StepFunctionCompute,
    StepFunctionComputeDomain,
)

__all__ = [
    "ComputeFactory",
    "IComputeLike",
    "GlueJobCompute",
    "GlueJobComputeDomain",
    "PyEntrypointCompute",
    "PyEntrypointComputeDomain",
    "PyEntrypointHandle",
    "StepFunctionCompute",
    "StepFunctionComputeDomain",
]
