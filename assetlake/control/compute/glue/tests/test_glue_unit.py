"""Unit tests for GlueJobCompute and GlueJobComputeDomain."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from assetlake.control.compute.base.factory import ComputeFactory
from assetlake.control.compute.base.protocol import IComputeLike
from assetlake.control.compute.glue.glue import GlueJobCompute, GlueJobComputeDomain
from assetlake.domain.compute.runtime import ComputeRuntime


def _make_client(run_states: list[str] | None = None) -> MagicMock:
    """Return a mock boto3 Glue client."""
    client = MagicMock()
    client.start_job_run.return_value = {"JobRunId": "run-abc"}
    if run_states:
        client.get_job_run.side_effect = [{"JobRun": {"JobRunState": s}} for s in run_states]
    return client


class TestGlueJobComputeDomain:
    """Test GlueJobComputeDomain model."""

    def test_init_required_fields(self):
        domain = GlueJobComputeDomain(name="my-glue-job")
        assert domain.name == "my-glue-job"
        assert domain.runtime == ComputeRuntime.GLUE

    def test_region_optional(self):
        domain = GlueJobComputeDomain(name="my-glue-job")
        assert domain.region is None

    def test_runtime_fixed_to_glue(self):
        domain = GlueJobComputeDomain(name="my-glue-job")
        assert domain.runtime == ComputeRuntime.GLUE


class TestGlueJobComputeInit:
    """Test GlueJobCompute instantiation."""

    def setup_method(self):
        """Ensure GlueJobCompute is registered before each test."""
        if ComputeRuntime.GLUE not in ComputeFactory._registry:
            ComputeFactory._registry[ComputeRuntime.GLUE] = GlueJobCompute

    def test_create_minimal(self):
        compute = GlueJobCompute(name="my-glue-job")
        assert compute.domain.name == "my-glue-job"
        assert compute.domain.region is None

    def test_protocol_compliance(self):
        compute = GlueJobCompute(name="my-glue-job")
        assert isinstance(compute, IComputeLike)

    def test_registered_in_factory(self):
        assert ComputeFactory._registry[ComputeRuntime.GLUE] is GlueJobCompute


class TestGlueJobComputeGetClient:
    """Test _get_client() boto3 session construction."""

    def test_raises_import_error_without_boto3(self):
        compute = GlueJobCompute(name="my-glue-job")
        with patch.dict("sys.modules", {"boto3": None}):
            with pytest.raises(ImportError, match="boto3"):
                compute._get_client()

    def test_returns_glue_client_without_access(self):
        compute = GlueJobCompute(name="my-glue-job")
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client

        with patch("boto3.Session", return_value=mock_session):
            result = compute._get_client()

        mock_session.client.assert_called_once_with("glue")
        assert result is mock_client

    def test_uses_access_credentials(self):
        from assetlake.control.access.aws.aws import AWSAccess

        compute = GlueJobCompute(name="my-glue-job")
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


class TestGlueJobComputeInspect:
    """Test inspect() run history listing."""

    def _make_run(
        self,
        run_id: str,
        state: str,
        started_on: datetime,
        completed_on: datetime | None = None,
    ) -> dict:
        return {
            "Id": run_id,
            "JobName": "my-job",
            "JobRunState": state,
            "StartedOn": started_on,
            "CompletedOn": completed_on,
            "ExecutionTime": 120,
            "ErrorMessage": None,
        }

    def _make_pages(self, runs: list[dict]) -> list[dict]:
        return [{"JobRuns": runs}]

    def test_inspect_returns_all_runs(self):
        compute = GlueJobCompute(name="my-glue-job")
        now = datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc)
        runs = [
            self._make_run("run-1", "SUCCEEDED", now),
            self._make_run("run-2", "FAILED", now),
        ]
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = self._make_pages(runs)
        client.get_paginator.return_value = paginator

        with patch.object(compute, "_get_client", return_value=client):
            results = compute.inspect()

        assert len(results) == 2
        assert results[0]["run_id"] == "run-1"
        assert results[1]["state"] == "FAILED"

    def test_inspect_since_filter(self):
        compute = GlueJobCompute(name="my-glue-job")
        since = datetime(2024, 6, 2, 0, 0, tzinfo=timezone.utc)
        runs = [
            self._make_run("run-1", "SUCCEEDED", datetime(2024, 6, 3, 0, 0, tzinfo=timezone.utc)),
            self._make_run("run-2", "SUCCEEDED", datetime(2024, 6, 1, 0, 0, tzinfo=timezone.utc)),
        ]
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = self._make_pages(runs)
        client.get_paginator.return_value = paginator

        with patch.object(compute, "_get_client", return_value=client):
            results = compute.inspect(since=since)

        assert len(results) == 1
        assert results[0]["run_id"] == "run-1"

    def test_inspect_until_filter(self):
        compute = GlueJobCompute(name="my-glue-job")
        until = datetime(2024, 6, 2, 0, 0, tzinfo=timezone.utc)
        runs = [
            self._make_run("run-1", "SUCCEEDED", datetime(2024, 6, 3, 0, 0, tzinfo=timezone.utc)),
            self._make_run("run-2", "SUCCEEDED", datetime(2024, 6, 1, 0, 0, tzinfo=timezone.utc)),
        ]
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = self._make_pages(runs)
        client.get_paginator.return_value = paginator

        with patch.object(compute, "_get_client", return_value=client):
            results = compute.inspect(until=until)

        assert len(results) == 1
        assert results[0]["run_id"] == "run-2"

    def test_inspect_limit(self):
        compute = GlueJobCompute(name="my-glue-job")
        now = datetime(2024, 6, 1, tzinfo=timezone.utc)
        runs = [self._make_run(f"run-{i}", "SUCCEEDED", now) for i in range(10)]
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = self._make_pages(runs)
        client.get_paginator.return_value = paginator

        with patch.object(compute, "_get_client", return_value=client):
            results = compute.inspect(limit=3)

        assert len(results) == 3

    def test_inspect_empty_pages(self):
        compute = GlueJobCompute(name="my-glue-job")
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = [{}]
        client.get_paginator.return_value = paginator

        with patch.object(compute, "_get_client", return_value=client):
            results = compute.inspect()

        assert results == []

    def test_inspect_raises_on_paginator_failure(self):
        compute = GlueJobCompute(name="my-glue-job")
        client = MagicMock()
        client.get_paginator.side_effect = Exception("access denied")

        with patch.object(compute, "_get_client", return_value=client):
            with pytest.raises(RuntimeError, match="access denied"):
                compute.inspect()

    def test_inspect_result_shape(self):
        compute = GlueJobCompute(name="my-glue-job")
        now = datetime(2024, 6, 1, tzinfo=timezone.utc)
        runs = [self._make_run("run-1", "SUCCEEDED", now, completed_on=now)]
        client = MagicMock()
        paginator = MagicMock()
        paginator.paginate.return_value = self._make_pages(runs)
        client.get_paginator.return_value = paginator

        with patch.object(compute, "_get_client", return_value=client):
            results = compute.inspect()

        r = results[0]
        assert set(r.keys()) == {
            "run_id",
            "name",
            "state",
            "started_on",
            "completed_on",
            "execution_time",
            "error_message",
        }
