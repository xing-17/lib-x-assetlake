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


class StepFunctionComputeDomain(AbstractComputeDomain):
    runtime: ComputeRuntime = ComputeRuntime.STEP_FUNCTION
    arn: str = Field(
        ...,
        description="State machine ARN",
    )
    region: str | None = Field(
        default=None,
        description="AWS region override",
    )


@ComputeFactory.add(ComputeRuntime.STEP_FUNCTION)
class StepFunctionCompute(
    IDomainObject,
    IComputeLike,
):
    _domain_class = StepFunctionComputeDomain

    def __init__(
        self,
        name: str,
        arn: str,
        region: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            name=name,
            runtime=ComputeRuntime.STEP_FUNCTION,
            arn=arn,
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
            return session.client("stepfunctions")
        except ImportError as e:
            raise ImportError("boto3 is required for StepFunctionCompute.") from e
        except Exception as e:
            raise RuntimeError(f"Failed to create Step Functions client: {e}") from e

    def inspect(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
        access: AWSAccess | None = None,
    ) -> list[dict[str, Any]]:
        _arn = self.domain.arn
        _client = self._get_client(access)
        try:
            paginator = _client.get_paginator("list_executions")
            pages = paginator.paginate(stateMachineArn=_arn)
        except Exception as e:
            error = f"Failed to list Step Functions executions for '{_arn}': {e}"
            raise RuntimeError(error) from e

        results: list[dict[str, Any]] = []
        for page in pages:
            for execution in page.get("executions", []):
                start_date: datetime | None = execution.get("startDate")
                if since and start_date and start_date < since:
                    continue
                if until and start_date and start_date > until:
                    continue
                results.append(
                    {
                        "execution_arn": execution.get("executionArn"),
                        "name": execution.get("name"),
                        "status": execution.get("status"),
                        "start_date": start_date,
                        "stop_date": execution.get("stopDate"),
                    }
                )
                if limit and len(results) >= limit:
                    return results
        return results
