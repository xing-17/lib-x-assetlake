from __future__ import annotations

from enum import StrEnum


class ComputeRuntime(StrEnum):
    """
    Enumeration of supported compute runtimes.

    Values:
        PY_ENTRYPOINT: Local Python entrypoint.
        FC: Alibaba Cloud Function Compute.
        LAMBDA: AWS Lambda.
        GLUE: AWS Glue.

    """

    PY_ENTRYPOINT = "py_entrypoint"
    FC = "fc"
    LAMBDA = "lambda"
    GLUE = "glue"
