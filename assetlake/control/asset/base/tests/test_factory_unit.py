"""Unit tests for asset base factory."""

from __future__ import annotations

import pytest

from assetlake.control.asset.base.factory import AssetFactory
from assetlake.domain.asset.filesystem import AssetFilesystem


class TestAssetFactory:
    """Test AssetFactory registration and loading."""

    def test_register_and_load_from_dict(self):
        """Test registering asset filesystem and loading from dict."""
        AssetFactory._registry.clear()

        @AssetFactory.add("test_filesystem")
        class TestAsset:
            @classmethod
            def from_dict(cls, data):
                return cls()

            @classmethod
            def from_domain(cls, domain):
                return cls()

        assert "test_filesystem" in AssetFactory._registry
        assert AssetFactory._registry["test_filesystem"] is TestAsset

    def test_register_duplicate_filesystem_raises(self):
        """Test duplicate filesystem registration raises ValueError."""
        AssetFactory._registry.clear()

        @AssetFactory.add("test_filesystem")
        class FirstAsset:
            pass

        with pytest.raises(ValueError, match="already registered"):

            @AssetFactory.add("test_filesystem")
            class SecondAsset:
                pass

    def test_load_from_dict(self):
        """Test loading asset from dictionary."""
        from assetlake.control.asset.local import LocalAsset

        AssetFactory._registry.clear()
        AssetFactory.add(AssetFilesystem.LOCAL)(LocalAsset)

        data = {
            "glob": "/path/**/*.parquet",
            "name": "test_asset",
            "filesystem": AssetFilesystem.LOCAL,
            "tags": {"env": "test"},
        }

        asset = AssetFactory.load(data)
        assert isinstance(asset, LocalAsset)
        assert asset.name == "test_asset"
        assert asset.filesystem == AssetFilesystem.LOCAL

    def test_load_from_domain_model(self):
        """Test loading asset from domain model."""
        from assetlake.control.asset.local import LocalAsset, LocalAssetDomain

        AssetFactory._registry.clear()
        AssetFactory.add(AssetFilesystem.LOCAL)(LocalAsset)

        domain = LocalAssetDomain(
            glob="/path/**/*.parquet",
            name="test_asset",
            tags={"env": "test"},
        )

        asset = AssetFactory.load(domain)
        assert isinstance(asset, LocalAsset)
        assert asset.name == "test_asset"
        assert asset.tags == {"env": "test"}

    def test_load_missing_filesystem_from_dict_raises(self):
        """Test loading without filesystem field from dict raises ValueError."""
        AssetFactory._registry.clear()

        with pytest.raises(ValueError, match="missing required field"):
            AssetFactory.load({"name": "test"})

    def test_load_unregistered_filesystem_raises(self):
        """Test loading unregistered filesystem raises ValueError."""
        AssetFactory._registry.clear()

        data = {
            "glob": "/path/**/*.parquet",
            "name": "test_asset",
            "filesystem": "nonexistent_filesystem",
        }

        with pytest.raises(ValueError, match="No asset registered"):
            AssetFactory.load(data)

    def test_register_decorator_returns_class(self):
        """Test add decorator returns the original class."""
        AssetFactory._registry.clear()

        @AssetFactory.add("test_filesystem")
        class TestAsset:
            pass

        assert TestAsset is not None
        assert TestAsset.__name__ == "TestAsset"
