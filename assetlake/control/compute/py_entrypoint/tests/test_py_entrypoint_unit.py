"""Unit tests for PyEntrypointCompute and PyEntrypointComputeDomain."""

from __future__ import annotations

from datetime import datetime

import pytest

from assetlake.control.access.local.local import LocalAccess
from assetlake.control.compute.base.factory import ComputeFactory
from assetlake.control.compute.base.protocol import IComputeLike
from assetlake.control.compute.py_entrypoint.handle import PyEntrypointHandle
from assetlake.control.compute.py_entrypoint.py_entrypoint import (
    PyEntrypointCompute,
    PyEntrypointComputeDomain,
    execute_in_queue,
)
from assetlake.domain.compute.runtime import ComputeRuntime


# Module-level helper functions for testing execute_in_queue
def _test_add(a, b):
    """Test function for addition."""
    return a + b


def _test_failing_func():
    """Test function that raises an error."""
    raise ValueError("test error")


def _test_multiply_with_default(x, y, z=10):
    """Test function with default parameter."""
    return x * y + z


def _test_count_items(items):
    """Test function that counts items."""
    return len(items)


def _test_join_paths(a, b):
    """Test function that joins paths."""
    import os

    return os.path.join(a, b)


class TestPyEntrypointComputeDomain:
    """Test PyEntrypointComputeDomain class."""

    def test_init(self):
        """Test domain initialization."""
        domain = PyEntrypointComputeDomain(
            name="test_compute",
            entrypoint="module.function",
            tags={"env": "test"},
        )
        assert domain.name == "test_compute"
        assert domain.runtime == ComputeRuntime.PY_ENTRYPOINT
        assert domain.entrypoint == "module.function"
        assert domain.tags == {"env": "test"}

    def test_runtime_fixed_to_py_entrypoint(self):
        """Test that runtime is fixed to PY_ENTRYPOINT."""
        domain = PyEntrypointComputeDomain(
            name="test",
            entrypoint="test.func",
        )
        assert domain.runtime == ComputeRuntime.PY_ENTRYPOINT

    def test_entrypoint_required(self):
        """Test that entrypoint is required."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            PyEntrypointComputeDomain(name="test")

    def test_tags_optional(self):
        """Test that tags are optional."""
        domain = PyEntrypointComputeDomain(
            name="test",
            entrypoint="test.func",
        )
        assert domain.tags is not None


class TestExecuteInQueue:
    """Test execute_in_queue helper function."""

    def test_execute_success(self):
        """Test successful function execution."""
        from multiprocessing import Queue

        queue = Queue()
        execute_in_queue(_test_add, {"a": 1, "b": 2}, queue)

        success, result = queue.get()
        assert success is True
        assert result == 3

    def test_execute_failure(self):
        """Test failed function execution."""
        from multiprocessing import Queue

        queue = Queue()
        execute_in_queue(_test_failing_func, {}, queue)

        success, result = queue.get()
        assert success is False
        assert isinstance(result, ValueError)
        assert str(result) == "test error"

    def test_execute_with_kwargs(self):
        """Test function execution with keyword arguments."""
        from multiprocessing import Queue

        queue = Queue()
        execute_in_queue(_test_multiply_with_default, {"x": 2, "y": 3, "z": 5}, queue)

        success, result = queue.get()
        assert success is True
        assert result == 11


class TestPyEntrypointCompute:
    """Test PyEntrypointCompute class."""

    def setup_method(self):
        """Ensure PyEntrypointCompute is registered before each test."""
        if ComputeRuntime.PY_ENTRYPOINT not in ComputeFactory._registry:
            ComputeFactory._registry[ComputeRuntime.PY_ENTRYPOINT] = PyEntrypointCompute

    def test_protocol_compliance(self):
        """Test that PyEntrypointCompute implements IComputeLike protocol."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="os.path.join",
            tags={"env": "test"},
        )
        assert isinstance(compute, IComputeLike)

    def test_init(self):
        """Test compute initialization."""
        compute = PyEntrypointCompute(
            name="test_compute",
            entrypoint="os.path.join",
            tags={"env": "test", "version": "1.0"},
        )
        assert compute.name == "test_compute"
        assert compute.runtime == ComputeRuntime.PY_ENTRYPOINT
        assert compute.domain.entrypoint == "os.path.join"
        assert compute.tags == {"env": "test", "version": "1.0"}

    def test_init_without_tags(self):
        """Test compute initialization without tags."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="os.path.join",
        )
        assert compute.tags is not None

    def test_factory_registration(self):
        """Test that PyEntrypointCompute is registered in factory."""
        assert ComputeRuntime.PY_ENTRYPOINT in ComputeFactory._registry
        assert ComputeFactory._registry[ComputeRuntime.PY_ENTRYPOINT] is PyEntrypointCompute

    def test_from_dict(self):
        """Test creating compute from dictionary."""
        data = {
            "name": "test_compute",
            "runtime": ComputeRuntime.PY_ENTRYPOINT,
            "entrypoint": "os.path.join",
            "tags": {"env": "prod"},
        }
        compute = PyEntrypointCompute.from_dict(data)
        assert compute.name == "test_compute"
        assert compute.runtime == ComputeRuntime.PY_ENTRYPOINT
        assert compute.domain.entrypoint == "os.path.join"
        assert compute.tags == {"env": "prod"}

    def test_from_domain(self):
        """Test creating compute from domain model."""
        domain = PyEntrypointComputeDomain(
            name="test_compute",
            entrypoint="os.path.join",
            tags={"env": "test"},
        )
        compute = PyEntrypointCompute.from_domain(domain)
        assert compute.name == "test_compute"
        assert compute.runtime == ComputeRuntime.PY_ENTRYPOINT
        assert compute.domain.entrypoint == "os.path.join"
        assert compute.tags == {"env": "test"}

    def test_resolve_entrypoint_builtin(self):
        """Test resolving built-in function entrypoint."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="os.path.join",
        )
        func = compute._resolve_entrypoint()
        assert callable(func)
        assert func.__name__ == "join"

    def test_resolve_entrypoint_invalid_module_raises(self):
        """Test that invalid module raises ImportError."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="nonexistent_module.function",
        )
        with pytest.raises(ImportError):
            compute._resolve_entrypoint()

    def test_resolve_entrypoint_invalid_function_raises(self):
        """Test that invalid function name raises AttributeError."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="os.path.nonexistent_function",
        )
        with pytest.raises(AttributeError):
            compute._resolve_entrypoint()

    def test_execute_simple_function(self):
        """Test executing a simple function."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="assetlake.control.compute.py_entrypoint.tests.test_py_entrypoint_unit._test_join_paths",
        )
        result = compute.execute(params={"a": "/home", "b": "user"})
        assert result == {"result": "/home/user"}

    def test_execute_with_access(self):
        """Test executing with access parameter."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="assetlake.control.compute.py_entrypoint.tests.test_py_entrypoint_unit._test_join_paths",
        )
        access = LocalAccess()
        result = compute.execute(params={"a": "/tmp", "b": "file.txt"}, access=access)
        assert result == {"result": "/tmp/file.txt"}

    def test_execute_without_params(self):
        """Test executing without parameters."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="os.getcwd",
        )
        result = compute.execute()
        assert "result" in result
        assert isinstance(result["result"], str)

    def test_execute_with_return_value(self):
        """Test executing function with return value."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="assetlake.control.compute.py_entrypoint.tests.test_py_entrypoint_unit._test_count_items",
        )
        result = compute.execute(params={"items": [1, 2, 3, 4, 5]})
        assert result == {"result": 5}

    def test_submit_returns_handle(self):
        """Test that submit returns a PyEntrypointHandle."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="assetlake.control.compute.py_entrypoint.tests.test_py_entrypoint_unit._test_join_paths",
        )
        handle = compute.submit(params={"a": "/home", "b": "user"})
        assert isinstance(handle, PyEntrypointHandle)
        assert handle.process is not None
        assert handle.queue is not None

        # Clean up
        result = handle.collect()
        assert result == {"result": "/home/user"}

    def test_submit_with_access(self):
        """Test submitting with access parameter."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="assetlake.control.compute.py_entrypoint.tests.test_py_entrypoint_unit._test_join_paths",
        )
        access = LocalAccess()
        handle = compute.submit(params={"a": "/tmp", "b": "file.txt"}, access=access)
        assert isinstance(handle, PyEntrypointHandle)

        # Clean up
        result = handle.collect()
        assert result == {"result": "/tmp/file.txt"}

    def test_submit_without_params(self):
        """Test submitting without parameters."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="os.getcwd",
        )
        handle = compute.submit()
        assert isinstance(handle, PyEntrypointHandle)

        # Clean up
        result = handle.collect()
        assert "result" in result
        assert isinstance(result["result"], str)

    def test_submit_and_collect(self):
        """Test submit and collect workflow."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="assetlake.control.compute.py_entrypoint.tests.test_py_entrypoint_unit._test_count_items",
        )
        handle = compute.submit(params={"items": [1, 2, 3]})
        result = handle.collect()
        assert result == {"result": 3}

    def test_inspect_returns_empty_list(self):
        """Test that inspect returns empty list (no-op)."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="os.path.join",
        )
        result = compute.inspect()
        assert result == []

    def test_inspect_with_parameters(self):
        """Test inspect with time parameters (no-op)."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="os.path.join",
        )
        access = LocalAccess()
        result = compute.inspect(
            since=datetime.now(),
            until=datetime.now(),
            limit=10,
            access=access,
        )
        assert result == []

    def test_export(self):
        """Test exporting compute to dictionary."""
        compute = PyEntrypointCompute(
            name="test_compute",
            entrypoint="os.path.join",
            tags={"env": "test"},
        )
        exported = compute.export()
        assert exported["name"] == "test_compute"
        assert exported["runtime"] == ComputeRuntime.PY_ENTRYPOINT
        assert exported["entrypoint"] == "os.path.join"
        assert exported["tags"] == {"env": "test"}

    def test_describe(self):
        """Test describing compute."""
        compute = PyEntrypointCompute(
            name="test_compute",
            entrypoint="os.path.join",
            tags={"env": "test"},
        )
        description = compute.describe()
        assert isinstance(description, str)
        assert len(description) > 0

    def test_domain_class_attribute(self):
        """Test that _domain_class is set correctly."""
        assert PyEntrypointCompute._domain_class is PyEntrypointComputeDomain

    def test_load_from_factory(self):
        """Test loading compute through factory."""
        data = {
            "name": "factory_test",
            "runtime": ComputeRuntime.PY_ENTRYPOINT,
            "entrypoint": "os.path.join",
            "tags": {"source": "factory"},
        }
        compute = ComputeFactory.load(data)
        assert isinstance(compute, PyEntrypointCompute)
        assert compute.name == "factory_test"
        assert compute.tags == {"source": "factory"}

    def test_multiple_executions(self):
        """Test executing compute multiple times."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="assetlake.control.compute.py_entrypoint.tests.test_py_entrypoint_unit._test_count_items",
        )
        result1 = compute.execute(params={"items": [1, 2]})
        result2 = compute.execute(params={"items": [1, 2, 3, 4]})

        assert result1 == {"result": 2}
        assert result2 == {"result": 4}

    def test_multiple_submissions(self):
        """Test submitting compute multiple times."""
        compute = PyEntrypointCompute(
            name="test",
            entrypoint="assetlake.control.compute.py_entrypoint.tests.test_py_entrypoint_unit._test_count_items",
        )
        handle1 = compute.submit(params={"items": [1, 2]})
        handle2 = compute.submit(params={"items": [1, 2, 3, 4]})

        result1 = handle1.collect()
        result2 = handle2.collect()

        assert result1 == {"result": 2}
        assert result2 == {"result": 4}
