"""Unit tests for GlueJobHandle."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from assetlake.control.compute.aws_glue.handle import GlueJobHandle
from assetlake.control.compute.base.protocol import ISubmitHandleLike


def _make_client(states: list[str], error_message: str = "") -> MagicMock:
    """Return a mock Glue client that cycles through the given JobRunStates."""
    client = MagicMock()
    responses = []
    for state in states:
        run = {"JobRunState": state}
        if error_message and state != "SUCCEEDED":
            run["ErrorMessage"] = error_message
        responses.append({"JobRun": run})
    client.get_job_run.side_effect = responses
    return client


class TestGlueJobHandleProtocol:
    """Test protocol compliance."""

    def test_implements_isubmithandlelike(self):
        handle = GlueJobHandle(client=MagicMock(), job="my_job", run_id="run-1")
        assert isinstance(handle, ISubmitHandleLike)

    def test_has_collect(self):
        handle = GlueJobHandle(client=MagicMock(), job="my_job", run_id="run-1")
        assert callable(handle.collect)


class TestGlueJobHandleInit:
    """Test handle initialisation."""

    def test_attributes_stored(self):
        client = MagicMock()
        handle = GlueJobHandle(client=client, job="my_job", run_id="run-42")
        assert handle._client is client
        assert handle._job == "my_job"
        assert handle._run_id == "run-42"

    def test_default_timeout(self):
        handle = GlueJobHandle(client=MagicMock(), job="j", run_id="r")
        assert handle._default_timeout == 3600


class TestGlueJobHandleCollect:
    """Test collect() polling logic."""

    def test_collect_succeeded_immediately(self):
        client = _make_client(["SUCCEEDED"])
        handle = GlueJobHandle(client=client, job="my_job", run_id="run-1")

        result = handle.collect(timeout=60)

        assert "result" in result
        client.get_job_run.assert_called_once_with(JobName="my_job", RunId="run-1")

    def test_collect_after_running_states(self):
        client = _make_client(["RUNNING", "RUNNING", "SUCCEEDED"])
        handle = GlueJobHandle(client=client, job="my_job", run_id="run-1")

        with pytest.MonkeyPatch().context() as mp:
            import time

            mp.setattr(time, "sleep", lambda _: None)
            result = handle.collect(timeout=60)

        assert "result" in result
        assert client.get_job_run.call_count == 3

    def test_collect_raises_on_failed(self):
        client = _make_client(["FAILED"], error_message="OOM")
        handle = GlueJobHandle(client=client, job="my_job", run_id="run-1")

        with pytest.raises(RuntimeError, match="failed at 'FAILED'"):
            handle.collect(timeout=60)

    def test_collect_raises_on_error_state(self):
        client = _make_client(["ERROR"], error_message="driver crashed")
        handle = GlueJobHandle(client=client, job="my_job", run_id="run-1")

        with pytest.raises(RuntimeError, match="failed at 'ERROR'"):
            handle.collect(timeout=60)

    def test_collect_raises_on_timeout(self):
        client = MagicMock()
        client.get_job_run.return_value = {"JobRun": {"JobRunState": "RUNNING"}}
        handle = GlueJobHandle(client=client, job="my_job", run_id="run-1")

        with pytest.MonkeyPatch().context() as mp:
            import time

            mp.setattr(time, "sleep", lambda _: None)
            with pytest.raises(TimeoutError, match="timeout after"):
                handle.collect(timeout=5)

    def test_collect_uses_default_timeout_when_none(self):
        client = MagicMock()
        client.get_job_run.return_value = {"JobRun": {"JobRunState": "RUNNING"}}
        handle = GlueJobHandle(client=client, job="my_job", run_id="run-1")

        resolved = handle._resolve_timeout(None)
        assert resolved == handle._default_timeout

    def test_collect_timeout_raises_timeout_error_not_runtime(self):
        client = MagicMock()
        client.get_job_run.return_value = {"JobRun": {"JobRunState": "RUNNING"}}
        handle = GlueJobHandle(client=client, job="my_job", run_id="run-1")

        with pytest.MonkeyPatch().context() as mp:
            import time

            mp.setattr(time, "sleep", lambda _: None)
            with pytest.raises(TimeoutError):
                handle.collect(timeout=5)

    def test_collect_stopped_raises(self):
        client = _make_client(["STOPPED"])
        handle = GlueJobHandle(client=client, job="my_job", run_id="run-1")

        with pytest.raises(RuntimeError, match="STOPPED"):
            handle.collect(timeout=60)
