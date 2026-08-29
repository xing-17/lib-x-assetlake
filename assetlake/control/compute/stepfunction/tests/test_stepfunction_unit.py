"""Unit tests for StepFunctionCompute and StepFunctionComputeDomain."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from assetlake.control.compute.base.factory import ComputeFactory
from assetlake.control.compute.base.protocol import IComputeLike
from assetlake.control.compute.stepfunction.stepfunction import (
    StepFunctionCompute,
    StepFunctionComputeDomain,
)
from assetlake.domain.compute.runtime import ComputeRuntime

_TEST_ARN = "arn:aws:states:us-east-1:123456789012:stateMachine:my-sfn"


class TestStepFunctionComputeDomain:
    def test_init_required_fields(self):
        domain = StepFunctionComputeDomain(name="my-sfn", arn=_TEST_ARN)
        assert domain.name == "my-sfn"
        assert domain.arn == _TEST_ARN
        assert domain.runtime == ComputeRuntime.STEP_FUNCTION

    def test_region_optional(self):
        domain = StepFunctionComputeDomain(name="my-sfn", arn=_TEST_ARN)
        assert domain.region is None

    def test_arn_required(self):
        with pytest.raises(Exception):
            StepFunctionComputeDomain(name="my-sfn")

    def test_runtime_fixed_to_step_function(self):
        domain = StepFunctionComputeDomain(name="my-sfn", arn=_TEST_ARN)
        assert domain.runtime == ComputeRuntime.STEP_FUNCTION


class TestStepFunctionComputeInit:
    def setup_method(self):
        if ComputeRuntime.STEP_FUNCTION not in ComputeFactory._registry:
            ComputeFactory._registry[ComputeRuntime.STEP_FUNCTION] = StepFunctionCompute

    def test_create_minimal(self):
        compute = StepFunctionCompute(name="my-sfn", arn=_TEST_ARN)
        assert compute.domain.name == "my-sfn"
        assert compute.domain.arn == _TEST_ARN
        assert compute.domain.region is None

    def test_create_with_all_fields(self):
        compute = StepFunctionCompute(
            name="my-sfn",
            arn=_TEST_ARN,
            region="us-east-1",
            tags={"env": "prod"},
        )
        assert compute.domain.region == "us-east-1"
        assert compute.tags == {"env": "prod"}

    def test_protocol_compliance(self):
        compute = StepFunctionCompute(name="my-sfn", arn=_TEST_ARN)
        assert isinstance(compute, IComputeLike)

    def test_registered_in_factory(self):
        assert ComputeFactory._registry[ComputeRuntime.STEP_FUNCTION] is StepFunctionCompute


class TestStepFunctionComputeGetClient:
    def test_raises_import_error_without_boto3(self):
        compute = StepFunctionCompute(name="my-sfn", arn=_TEST_ARN)
        with patch.dict("sys.modules", {"boto3": None}):
            with pytest.raises(ImportError, match="boto3"):
                compute._get_client()

    def test_returns_stepfunctions_client_without_access(self):
        compute = StepFunctionCompute(name="my-sfn", arn=_TEST_ARN)
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client

        with patch("boto3.Session", return_value=mock_session):
            result = compute._get_client()

        mock_session.client.assert_called_once_with("stepfunctions")
        assert result is mock_client

    def test_uses_access_credentials(self):
        from assetlake.control.access.aws.aws import AWSAccess

        compute = StepFunctionCompute(name="my-sfn", arn=_TEST_ARN)
        access = AWSAccess(
            name="test_access",
            access_key_id="AKID",
            access_key_secret="SECRET",
        )
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()

        with patch("boto3.Session", return_value=mock_session) as mock_boto3:
            compute._get_client(access=access)

        call_kwargs = mock_boto3.call_args.kwargs
        assert call_kwargs["aws_access_key_id"] == "AKID"
        assert call_kwargs["aws_secret_access_key"] == "SECRET"


class TestStepFunctionComputeInspect:
    def _make_execution(
        self,
        execution_arn: str,
        name: str,
        status: str,
        start_date: datetime,
        stop_date: datetime | None = None,
    ) -> dict:
        return {
            "executionArn": execution_arn,
            "stateMachineArn": _TEST_ARN,
            "name": name,
            "status": status,
            "startDate": start_date,
            "stopDate": stop_date,
        }

    def _make_pages(self, executions: list[dict]) -> list[dict]:
        return [{"executions": executions}]

    def test_inspect_returns_all_executions(self):
        compute = StepFunctionCompute(name="my-sfn", arn=_TEST_ARN)
        now = datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc)
        executions = [
            self._make_execution("arn:exec-1", "run-1", "SUCCEEDED", now),
            self._make_execution("arn:exec-2", "run-2", "FAILED", now),
        ]
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = self._make_pages(executions)
        client.get_paginator.return_value = paginator

        with patch.object(compute, "_get_client", return_value=client):
            results = compute.inspect()

        assert len(results) == 2
        assert results[0]["execution_arn"] == "arn:exec-1"
        assert results[1]["status"] == "FAILED"

    def test_inspect_since_filter(self):
        compute = StepFunctionCompute(name="my-sfn", arn=_TEST_ARN)
        since = datetime(2024, 6, 2, 0, 0, tzinfo=timezone.utc)
        executions = [
            self._make_execution(
                "arn:exec-1", "run-1", "SUCCEEDED", datetime(2024, 6, 3, 0, 0, tzinfo=timezone.utc)
            ),
            self._make_execution(
                "arn:exec-2", "run-2", "SUCCEEDED", datetime(2024, 6, 1, 0, 0, tzinfo=timezone.utc)
            ),
        ]
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = self._make_pages(executions)
        client.get_paginator.return_value = paginator

        with patch.object(compute, "_get_client", return_value=client):
            results = compute.inspect(since=since)

        assert len(results) == 1
        assert results[0]["execution_arn"] == "arn:exec-1"

    def test_inspect_until_filter(self):
        compute = StepFunctionCompute(name="my-sfn", arn=_TEST_ARN)
        until = datetime(2024, 6, 2, 0, 0, tzinfo=timezone.utc)
        executions = [
            self._make_execution(
                "arn:exec-1", "run-1", "SUCCEEDED", datetime(2024, 6, 3, 0, 0, tzinfo=timezone.utc)
            ),
            self._make_execution(
                "arn:exec-2", "run-2", "SUCCEEDED", datetime(2024, 6, 1, 0, 0, tzinfo=timezone.utc)
            ),
        ]
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = self._make_pages(executions)
        client.get_paginator.return_value = paginator

        with patch.object(compute, "_get_client", return_value=client):
            results = compute.inspect(until=until)

        assert len(results) == 1
        assert results[0]["execution_arn"] == "arn:exec-2"

    def test_inspect_limit(self):
        compute = StepFunctionCompute(name="my-sfn", arn=_TEST_ARN)
        now = datetime(2024, 6, 1, tzinfo=timezone.utc)
        executions = [
            self._make_execution(f"arn:exec-{i}", f"run-{i}", "SUCCEEDED", now) for i in range(10)
        ]
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = self._make_pages(executions)
        client.get_paginator.return_value = paginator

        with patch.object(compute, "_get_client", return_value=client):
            results = compute.inspect(limit=3)

        assert len(results) == 3

    def test_inspect_empty_pages(self):
        compute = StepFunctionCompute(name="my-sfn", arn=_TEST_ARN)
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [{}]
        client.get_paginator.return_value = paginator

        with patch.object(compute, "_get_client", return_value=client):
            results = compute.inspect()

        assert results == []

    def test_inspect_raises_on_paginator_failure(self):
        compute = StepFunctionCompute(name="my-sfn", arn=_TEST_ARN)
        client = MagicMock()
        client.get_paginator.side_effect = Exception("access denied")

        with patch.object(compute, "_get_client", return_value=client):
            with pytest.raises(RuntimeError, match="access denied"):
                compute.inspect()

    def test_inspect_result_shape(self):
        compute = StepFunctionCompute(name="my-sfn", arn=_TEST_ARN)
        now = datetime(2024, 6, 1, tzinfo=timezone.utc)
        executions = [self._make_execution("arn:exec-1", "run-1", "SUCCEEDED", now, stop_date=now)]
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = self._make_pages(executions)
        client.get_paginator.return_value = paginator

        with patch.object(compute, "_get_client", return_value=client):
            results = compute.inspect()

        r = results[0]
        assert set(r.keys()) == {"execution_arn", "name", "status", "start_date", "stop_date"}
