from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from assetlake.control.access.aws.aws import AWSAccess
from assetlake.control.compute.base.factory import ComputeFactory
from assetlake.control.compute.base.protocol import IComputeLike
from assetlake.domain.compute.compute import AbstractComputeDomain
from assetlake.domain.compute.runtime import ComputeRuntime
from assetlake.internal.idomainobject import IDomainObject


class GlueJobComputeDomain(AbstractComputeDomain):
    runtime: ComputeRuntime = ComputeRuntime.GLUE
    region: str | None = Field(
        default=None,
        description="AWS region override",
    )


@ComputeFactory.add(ComputeRuntime.GLUE)
class GlueJobCompute(
    IDomainObject,
    IComputeLike,
):
    _domain_class = GlueJobComputeDomain

    def __init__(
        self,
        name: str,
        region: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            name=name,
            runtime=ComputeRuntime.GLUE,
            region=region,
            tags=tags,
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

    def inspect(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
        access: AWSAccess | None = None,
    ) -> list[dict[str, Any]]:
        _job = self.domain.name
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
                        "name": run.get("JobName"),
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
