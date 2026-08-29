"""Unit tests for PyEntrypointHandle."""

from __future__ import annotations

from multiprocessing import Process, Queue

import pytest

from assetlake.control.compute.py_entrypoint.handle import PyEntrypointHandle


# Module-level worker functions for multiprocessing (must be picklable)
def _worker_success(q):
    """Worker that puts a successful result."""
    q.put((True, 42))


def _worker_failure(q):
    """Worker that puts a failed result."""
    q.put((False, ValueError("test error")))


def _worker_complex(q):
    """Worker that puts a complex result."""
    q.put((True, {"nested": {"data": [1, 2, 3]}, "count": 10}))


def _worker_none(q):
    """Worker that puts None result."""
    q.put((True, None))


class TestPyEntrypointHandle:
    """Test PyEntrypointHandle class."""

    def test_init(self):
        """Test handle initialization."""
        queue = Queue()
        process = Process(target=lambda: None, daemon=True)

        handle = PyEntrypointHandle(process=process, queue=queue)
        assert handle.process is process
        assert handle.queue is queue

    def test_collect_success(self):
        """Test collecting successful result."""
        queue = Queue()
        process = Process(target=_worker_success, args=(queue,), daemon=True)
        process.start()

        handle = PyEntrypointHandle(process=process, queue=queue)
        result = handle.collect()

        assert result == {"result": 42}
        assert not process.is_alive()

    def test_collect_failure_raises(self):
        """Test collecting failed result raises exception."""
        queue = Queue()
        process = Process(target=_worker_failure, args=(queue,), daemon=True)
        process.start()

        handle = PyEntrypointHandle(process=process, queue=queue)

        with pytest.raises(ValueError, match="test error"):
            handle.collect()

        assert not process.is_alive()

    def test_collect_with_complex_result(self):
        """Test collecting complex result types."""
        queue = Queue()
        process = Process(target=_worker_complex, args=(queue,), daemon=True)
        process.start()

        handle = PyEntrypointHandle(process=process, queue=queue)
        result = handle.collect()

        assert result == {"result": {"nested": {"data": [1, 2, 3]}, "count": 10}}
        assert not process.is_alive()

    def test_collect_with_none_result(self):
        """Test collecting None result."""
        queue = Queue()
        process = Process(target=_worker_none, args=(queue,), daemon=True)
        process.start()

        handle = PyEntrypointHandle(process=process, queue=queue)
        result = handle.collect()

        assert result == {"result": None}
        assert not process.is_alive()
