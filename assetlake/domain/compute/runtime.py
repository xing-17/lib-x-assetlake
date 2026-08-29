from __future__ import annotations

from enum import StrEnum


class ComputeRuntime(StrEnum):
    """
    Enumeration of supported compute runtimes.

    Values:
        PY_ENTRYPOINT: Local Python entrypoint.
        FC: Alibaba Cloud Function Compute.
        GLUE: AWS Glue.
        STEP_FUNCTION: AWS Step Functions.

    """

    PY_ENTRYPOINT = "py_entrypoint"
    FC = "fc"
    GLUE = "glue"
    STEP_FUNCTION = "step_function"
