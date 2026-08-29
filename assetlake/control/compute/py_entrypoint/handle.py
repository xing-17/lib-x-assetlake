from __future__ import annotations

from multiprocessing import Process, Queue
from typing import Any


class PyEntrypointHandle:
    """
    Handle class for managing asynchronous execution of tasks.

    Attributes:
        process (Process): The process executing the task.
        queue (Queue): The queue for inter-process communication.

    Methods:
        collect(): Wait for the process to complete and return the result.

    """

    _default_timeout: int = 3600  # seconds

    def __init__(
        self,
        process: Process,
        queue: Queue,
    ) -> None:
        self.process = process
        self.queue = queue

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
        _timeout = self._resolve_timeout(timeout)
        success, result = self.queue.get(timeout=_timeout)
        self.process.join(timeout=_timeout)
        if not success:
            raise result
        return {"result": result}
