from __future__ import annotations

from multiprocessing import Process, Queue
from typing import Any

from assetlake.control.compute.base.protocol import ISubmitHandleLike


class PyEntrypointHandle(ISubmitHandleLike):
    """
    Handle class for managing asynchronous execution of tasks.

    Attributes:
        process (Process): The process executing the task.
        queue (Queue): The queue for inter-process communication.

    Methods:
        collect(): Wait for the process to complete and return the result.

    """

    def __init__(
        self,
        process: Process,
        queue: Queue,
    ) -> None:
        self.process = process
        self.queue = queue

    def collect(self) -> dict[str, Any]:
        success, result = self.queue.get()
        self.process.join()
        if not success:
            raise result
        return {"result": result}
