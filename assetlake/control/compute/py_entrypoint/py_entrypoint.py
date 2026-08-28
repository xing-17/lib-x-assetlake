from __future__ import annotations

import importlib
from datetime import datetime
from multiprocessing import Process, Queue
from typing import Any, Callable

from pydantic import Field

from assetlake.control.access.local.local import LocalAccess
from assetlake.control.compute.base.factory import ComputeFactory
from assetlake.control.compute.base.protocol import IComputeLike
from assetlake.control.compute.py_entrypoint.handle import PyEntrypointHandle
from assetlake.domain.compute.compute import AbstractComputeDomain
from assetlake.domain.compute.runtime import ComputeRuntime
from assetlake.internal.idomainobject import IDomainObject


def execute_in_queue(
    func: Callable[..., Any],
    params: dict[str, Any],
    queue: Queue,
) -> None:
    try:
        result = func(**params)
        queue.put((True, result))
    except Exception as exc:
        queue.put((False, exc))


class PyEntrypointComputeDomain(AbstractComputeDomain):
    """
    Python Entrypoint Compute Domain class for managing Python entrypoint computations.

    Attributes:
        name: Name of the compute.
        runtime: The compute runtime, fixed to PY_ENTRYPOINT.
        sync: Whether the compute is synchronous or asynchronous.
        entrypoint: The Python entrypoint to execute.
        tags: Tags associated with the compute.

    """

    runtime: ComputeRuntime = ComputeRuntime.PY_ENTRYPOINT
    entrypoint: str = Field(
        ...,
        description="The Python entrypoint to execute",
    )


@ComputeFactory.add(ComputeRuntime.PY_ENTRYPOINT)
class PyEntrypointCompute(
    IDomainObject,
    IComputeLike,
):
    """
    Python Entrypoint Compute class for managing Python entrypoint computations.

    Attributes:
        name: Name of the compute.
        entrypoint: The Python entrypoint to execute.
        tags: Tags associated with the compute.

    """

    _domain_class = PyEntrypointComputeDomain

    def __init__(
        self,
        name: str,
        entrypoint: str,
        tags: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            name=name,
            runtime=ComputeRuntime.PY_ENTRYPOINT,
            entrypoint=entrypoint,
            tags=tags,
        )

    def _resolve_entrypoint(self) -> Callable[..., Any]:
        module_path, func_name = self.domain.entrypoint.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, func_name)

    def execute(
        self,
        params: dict[str, Any] | None = None,
        access: LocalAccess | None = None,
    ) -> dict[str, Any]:
        # Access only for granularity
        if params is None:
            params = {}
        _callable = self._resolve_entrypoint()
        result = _callable(**params)
        return {"result": result}

    def submit(
        self,
        params: dict[str, Any] | None = None,
        access: LocalAccess | None = None,
    ) -> PyEntrypointHandle:
        # Access only for granularity
        if params is None:
            params = {}
        _callable = self._resolve_entrypoint()
        queue = Queue()
        process = Process(
            target=execute_in_queue,
            args=(_callable, params, queue),
            daemon=True,
        )
        process.start()
        handle = PyEntrypointHandle(
            process=process,
            queue=queue,
        )
        return handle

    def inspect(
        self,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
        access: LocalAccess | None = None,
    ) -> list[dict[str, Any]]:
        # No-ops
        return []
