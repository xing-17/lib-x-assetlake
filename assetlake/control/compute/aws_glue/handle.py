from __future__ import annotations

import time
from typing import Any

from assetlake.control.compute.aws_glue._constants import _TERMINAL_STATES
from assetlake.control.compute.base.protocol import ISubmitHandleLike


class GlueJobHandle(ISubmitHandleLike):
    """
    Handle for an asynchronously submitted AWS Glue job run.

    Attributes:
        _client: The boto3 Glue client.
        _job_name: The Glue job name.
        _run_id: The Glue job run ID.

    Methods:
        collect(): Poll until the run reaches a terminal state and return the result.

    """

    _default_interval = 10  # seconds
    _default_timeout = 3600  # seconds

    def __init__(
        self,
        client: Any,
        job: str,
        run_id: str,
    ) -> None:
        self._client = client
        self._job = job
        self._run_id = run_id

    def _resolve_timeout(
        self,
        timeout: int | None = None,
    ) -> int:
        if timeout is None:
            return self._default_timeout
        return timeout

    def collect(
        self,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        _interval = self._default_interval
        _timeout = self._resolve_timeout(timeout)
        _iters = max(1, _timeout // _interval)
        for _ in range(_iters):
            _resp = self._client.get_job_run(
                JobName=self._job,
                RunId=self._run_id,
            )
            _job = self._job
            _rid = self._run_id
            _run = _resp["JobRun"]
            state = _run["JobRunState"]
            if state in _TERMINAL_STATES:
                if state != "SUCCEEDED":
                    msg = _run.get("ErrorMessage", "")
                    error = f"Job '{_job}' run '{_rid}' failed at '{state}': {msg}"
                    raise RuntimeError(error)
                return {"result": _resp}
            else:
                time.sleep(_interval)

        error = f"Job '{_job}' run '{_rid}' timeout after {_timeout} seconds."
        raise TimeoutError(error)
