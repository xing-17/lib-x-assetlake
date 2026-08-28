"""Unit tests for compute base protocol."""

from __future__ import annotations

from assetlake.control.compute.base.protocol import IComputeLike, ISubmitHandleLike
from assetlake.domain.compute.runtime import ComputeRuntime


class TestISubmitHandleLike:
    """Test ISubmitHandleLike protocol."""

    def test_protocol_runtime_checkable(self):
        """Test that ISubmitHandleLike is runtime checkable."""

        class ConcreteSubmitHandle:
            def collect(self):
                return {"status": "success"}

        instance = ConcreteSubmitHandle()
        assert isinstance(instance, ISubmitHandleLike)

    def test_protocol_missing_method_fails_check(self):
        """Test that missing protocol methods fail instance check."""

        class IncompleteSubmitHandle:
            pass

        instance = IncompleteSubmitHandle()
        assert not isinstance(instance, ISubmitHandleLike)

    def test_protocol_has_collect_method(self):
        """Test that protocol requires collect method."""
        from assetlake.control.compute.py_entrypoint import PyEntrypointHandle

        handle = PyEntrypointHandle(queue=None, process=None)
        assert hasattr(handle, "collect")


class TestIComputeLike:
    """Test IComputeLike protocol."""

    def test_protocol_runtime_checkable(self):
        """Test that IComputeLike is runtime checkable."""

        class ConcreteCompute:
            name: str = "test"
            runtime: ComputeRuntime = ComputeRuntime.PY_ENTRYPOINT
            tags: dict[str, str] = {}

            @classmethod
            def from_dict(cls, data):
                return cls()

            @classmethod
            def from_domain(cls, domain):
                return cls()

            def execute(self, params=None, access=None):
                return {}

            def submit(self, params=None, access=None):
                class Handle:
                    def collect(self):
                        return {}

                return Handle()

            def inspect(self, since=None, until=None, limit=None, access=None):
                return []

            def export(self):
                return {}

            def describe(self):
                return "test compute"

        instance = ConcreteCompute()
        assert isinstance(instance, IComputeLike)

    def test_protocol_missing_method_fails_check(self):
        """Test that missing protocol methods fail instance check."""

        class IncompleteCompute:
            name: str = "test"
            runtime: ComputeRuntime = ComputeRuntime.PY_ENTRYPOINT
            tags: dict[str, str] = {}
            # Missing from_dict, from_domain, execute, submit, inspect, export, describe

        instance = IncompleteCompute()
        assert not isinstance(instance, IComputeLike)

    def test_protocol_has_required_attributes(self):
        """Test that protocol requires name, runtime, tags."""
        from assetlake.control.compute.py_entrypoint import PyEntrypointCompute

        compute = PyEntrypointCompute(
            name="test",
            entrypoint="module.function",
            tags={"env": "test"},
        )

        assert hasattr(compute, "name")
        assert hasattr(compute, "runtime")
        assert hasattr(compute, "tags")

    def test_protocol_has_required_methods(self):
        """Test that protocol requires from_dict, from_domain, execute, submit, inspect, export, describe."""
        from assetlake.control.compute.py_entrypoint import PyEntrypointCompute

        assert hasattr(PyEntrypointCompute, "from_dict")
        assert hasattr(PyEntrypointCompute, "from_domain")
        assert hasattr(PyEntrypointCompute, "execute")
        assert hasattr(PyEntrypointCompute, "submit")
        assert hasattr(PyEntrypointCompute, "inspect")
        assert hasattr(PyEntrypointCompute, "export")
        assert hasattr(PyEntrypointCompute, "describe")

    def test_protocol_execute_signature(self):
        """Test that execute method accepts params and access."""
        from assetlake.control.compute.py_entrypoint import PyEntrypointCompute

        compute = PyEntrypointCompute(
            name="test",
            entrypoint="os.getcwd",
            tags={},
        )

        # Should accept these parameters without error
        result = compute.execute(params={}, access=None)
        assert isinstance(result, dict)

    def test_protocol_submit_returns_handle(self):
        """Test that submit method returns ISubmitHandleLike."""
        from assetlake.control.compute.py_entrypoint import PyEntrypointCompute

        compute = PyEntrypointCompute(
            name="test",
            entrypoint="os.getcwd",
            tags={},
        )

        handle = compute.submit(params={}, access=None)
        assert isinstance(handle, ISubmitHandleLike)

    def test_protocol_inspect_returns_list(self):
        """Test that inspect method returns list."""
        from assetlake.control.compute.py_entrypoint import PyEntrypointCompute

        compute = PyEntrypointCompute(
            name="test",
            entrypoint="os.getcwd",
            tags={},
        )

        result = compute.inspect(
            since=None,
            until=None,
            limit=10,
            access=None,
        )
        assert isinstance(result, list)
