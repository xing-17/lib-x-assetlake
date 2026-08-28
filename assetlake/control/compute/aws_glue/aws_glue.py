from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from pydantic import Field

from assetlake.control.access.aws.aws import AWSAccess
from assetlake.control.compute.aws_glue._constants import _TERMINAL_STATES
from assetlake.control.compute.aws_glue.handle import GlueJobHandle
from assetlake.control.compute.base.factory import ComputeFactory
from assetlake.control.compute.base.protocol import IComputeLike
from assetlake.domain.compute.compute import AbstractComputeDomain
from assetlake.domain.compute.runtime import ComputeRuntime
from assetlake.internal.idomainobject import IDomainObject


class GlueJobComputeDomain(AbstractComputeDomain):
    runtime: ComputeRuntime = ComputeRuntime.GLUE
    job_name: str = Field(
        ...,
        description="AWS Glue job name",
    )
    region: str | None = Field(
        default=None,
        description="AWS region override",
    )
    default_args: dict[str, str] = Field(
        default_factory=dict,
        description="Default job arguments (keys prefixed with '--')",
    )


@ComputeFactory.add(ComputeRuntime.GLUE)
class GlueJobCompute(
    IDomainObject,
    IComputeLike,
):
    _domain_class = GlueJobComputeDomain
    _default_timeout = 3600  # seconds
    _default_interval = 10  # seconds

    def __init__(
        self,
        name: str,
        job_name: str,
        region: str | None = None,
        default_args: dict[str, str] | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            name=name,
            runtime=ComputeRuntime.GLUE,
            job_name=job_name,
            region=region,
            default_args=default_args or {},
            tags=tags or {},
        )

    def _get_client(
        self,
        access: AWSAccess | None = None,
    ) -> Any:
        try:
            import boto3

            if access:
                session = boto3.Session(
                    aws_access_key_id=access.access_key_id,
                    aws_secret_access_key=access.access_key_secret,
                    aws_session_token=access.session_token,
                    profile_name=access.profile,
                    region_name=access.region or self.domain.region,
                )
            else:
                session = boto3.Session()
            return session.client("glue")
        except ImportError as e:
            raise ImportError("boto3 is required for GlueJobCompute.") from e
        except Exception as e:
            raise RuntimeError(f"Failed to create Glue client: {e}") from e

    def _build_args(
        self,
        params: dict[str, Any] | None,
    ) -> dict[str, str]:
        args = dict(self.domain.default_args)
        if params:
            for k, v in params.items():
                key = k if k.startswith("--") else f"--{k}"
                args[key] = str(v)
        return args

    def execute(
        self,
        params: dict[str, Any] | None = None,
        access: AWSAccess | None = None,
        interval: int = 5,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        _timeout = timeout or self._default_timeout
        _interval = interval or self._default_interval
        _iters = max(1, _timeout // _interval)
        _job = self.domain.job_name
        _client = self._get_client(access)
        _args = self._build_args(params)
        try:
            response = _client.start_job_run(
                JobName=_job,
                Arguments=_args,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start job '{_job}': {e}") from e

        _rid: str = response["JobRunId"]
        for _ in range(_iters):
            _resp = _client.get_job_run(
                JobName=_job,
                RunId=_rid,
            )
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

    def submit(
        self,
        params: dict[str, Any] | None = None,
        access: AWSAccess | None = None,
    ) -> GlueJobHandle:
        _job = self.domain.job_name
        _client = self._get_client(access)
        _args = self._build_args(params)
        try:
            response = _client.start_job_run(
                JobName=_job,
                Arguments=_args,
            )
        except Exception as e:
            _error = f"Failed to submit Glue job '{_job}': {e}"
            raise RuntimeError(_error) from e

        run_id: str = response["JobRunId"]
        return GlueJobHandle(
            client=_client,
            job=_job,
            run_id=run_id,
        )

    def inspect(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
        access: AWSAccess | None = None,
    ) -> list[dict[str, Any]]:
        _job = self.domain.job_name
        _client = self._get_client(access)
        try:
            paginator = _client.get_paginator("get_job_runs")
            pages = paginator.paginate(JobName=_job)
        except Exception as e:
            error = f"Failed to list Glue job runs for '{_job}': {e}"
            raise RuntimeError(error) from e

        results: list[dict[str, Any]] = []
        for page in pages:
            for run in page.get("JobRuns", []):
                started_on: datetime | None = run.get("StartedOn")
                if since and started_on and started_on < since:
                    continue
                if until and started_on and started_on > until:
                    continue
                results.append(
                    {
                        "run_id": run.get("Id"),
                        "job_name": run.get("JobName"),
                        "state": run.get("JobRunState"),
                        "started_on": started_on,
                        "completed_on": run.get("CompletedOn"),
                        "execution_time": run.get("ExecutionTime"),
                        "error_message": run.get("ErrorMessage"),
                    }
                )
                if limit and len(results) >= limit:
                    return results
        return results
