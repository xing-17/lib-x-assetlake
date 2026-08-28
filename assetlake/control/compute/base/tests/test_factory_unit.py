"""Unit tests for compute base factory."""

from __future__ import annotations

import pytest

from assetlake.control.compute.base.factory import ComputeFactory
from assetlake.domain.compute.runtime import ComputeRuntime


class TestComputeFactory:
    """Test ComputeFactory registration and loading."""

    def test_register_and_load_from_dict(self):
        """Test registering compute runtime and loading from dict."""
        ComputeFactory._registry.clear()

        @ComputeFactory.add("test_runtime")
        class TestCompute:
            @classmethod
            def from_dict(cls, data):
                return cls()

            @classmethod
            def from_domain(cls, domain):
                return cls()

        assert "test_runtime" in ComputeFactory._registry
        assert ComputeFactory._registry["test_runtime"] is TestCompute

    def test_register_duplicate_runtime_raises(self):
        """Test duplicate runtime registration raises ValueError."""
        ComputeFactory._registry.clear()

        @ComputeFactory.add("test_runtime")
        class FirstCompute:
            pass

        with pytest.raises(ValueError, match="already registered"):

            @ComputeFactory.add("test_runtime")
            class SecondCompute:
                pass

    def test_load_from_dict(self):
        """Test loading compute from dictionary."""
        from assetlake.control.compute.py_entrypoint import PyEntrypointCompute

        ComputeFactory._registry.clear()
        ComputeFactory.add(ComputeRuntime.PY_ENTRYPOINT)(PyEntrypointCompute)

        data = {
            "name": "test_compute",
            "runtime": ComputeRuntime.PY_ENTRYPOINT,
            "entrypoint": "module.function",
            "tags": {"env": "test"},
        }

        compute = ComputeFactory.load(data)
        assert isinstance(compute, PyEntrypointCompute)
        assert compute.name == "test_compute"
        assert compute.runtime == ComputeRuntime.PY_ENTRYPOINT

    def test_load_from_domain_model(self):
        """Test loading compute from domain model."""
        from assetlake.control.compute.py_entrypoint import (
            PyEntrypointCompute,
            PyEntrypointComputeDomain,
        )

        ComputeFactory._registry.clear()
        ComputeFactory.add(ComputeRuntime.PY_ENTRYPOINT)(PyEntrypointCompute)

        domain = PyEntrypointComputeDomain(
            name="test_compute",
            entrypoint="module.function",
            tags={"env": "test"},
        )

        compute = ComputeFactory.load(domain)
        assert isinstance(compute, PyEntrypointCompute)
        assert compute.name == "test_compute"
        assert compute.tags == {"env": "test"}

    def test_load_missing_runtime_from_dict_raises(self):
        """Test loading without runtime field from dict raises ValueError."""
        ComputeFactory._registry.clear()

        with pytest.raises(ValueError, match="missing required field"):
            ComputeFactory.load({"name": "test"})

    def test_load_unregistered_runtime_raises(self):
        """Test loading unregistered runtime raises ValueError."""
        ComputeFactory._registry.clear()

        data = {
            "name": "test_compute",
            "runtime": "nonexistent_runtime",
            "entrypoint": "module.function",
        }

        with pytest.raises(ValueError, match="No compute registered"):
            ComputeFactory.load(data)

    def test_register_decorator_returns_class(self):
        """Test add decorator returns the original class."""
        ComputeFactory._registry.clear()

        @ComputeFactory.add("test_runtime")
        class TestCompute:
            pass

        assert TestCompute is not None
        assert TestCompute.__name__ == "TestCompute"
