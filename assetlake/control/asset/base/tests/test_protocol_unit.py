"""Unit tests for asset base protocol."""

from __future__ import annotations

from datetime import datetime

from assetlake.control.asset.base.protocol import IAssetLike, IAssetObjectLike
from assetlake.domain.asset.filesystem import AssetFilesystem
from assetlake.domain.asset.objectkind import AssetObjectkind


class TestIAssetObjectLike:
    """Test IAssetObjectLike protocol."""

    def test_protocol_runtime_checkable(self):
        """Test that IAssetObjectLike is runtime checkable."""

        class ConcreteAssetObject:
            uri: str = "file:///path/to/object"
            size: int | None = 1024
            modified_at: datetime | None = datetime.now()
            partitions: dict[str, str] = {}

            @classmethod
            def from_dict(cls, data):
                return cls()

            def describe(self):
                return "test asset object"

            def export(self):
                return {}

        instance = ConcreteAssetObject()
        assert isinstance(instance, IAssetObjectLike)

    def test_protocol_missing_method_fails_check(self):
        """Test that missing protocol methods fail instance check."""

        class IncompleteAssetObject:
            uri: str = "file:///path/to/object"
            size: int | None = 1024
            modified_at: datetime | None = datetime.now()
            partitions: dict[str, str] = {}
            # Missing from_dict, describe, export

        instance = IncompleteAssetObject()
        assert not isinstance(instance, IAssetObjectLike)

    def test_protocol_has_required_attributes(self):
        """Test that protocol requires uri, size, modified_at, partitions."""
        from assetlake.control.asset.local.object import LocalAssetObject

        obj = LocalAssetObject(
            uri="file:///path/to/test",
            size=1024,
            modified_at=datetime.now(),
        )

        assert hasattr(obj, "uri")
        assert hasattr(obj, "size")
        assert hasattr(obj, "modified_at")
        assert hasattr(obj, "partitions")

    def test_protocol_has_required_methods(self):
        """Test that protocol requires from_dict, describe, export."""
        from assetlake.control.asset.local.object import LocalAssetObject

        assert hasattr(LocalAssetObject, "from_dict")
        assert hasattr(LocalAssetObject, "describe")
        assert hasattr(LocalAssetObject, "export")


class TestIAssetLike:
    """Test IAssetLike protocol."""

    def test_protocol_runtime_checkable(self):
        """Test that IAssetLike is runtime checkable."""

        class ConcreteAsset:
            glob: str = "/path/**/*.parquet"
            name: str | None = "test"
            filesystem: AssetFilesystem = AssetFilesystem.LOCAL
            objectkind: AssetObjectkind = AssetObjectkind.PARQUET
            partitions: list[str] | None = []
            description: str | None = "test description"
            owner: str | None = "test_owner"
            metadata: dict[str, any] = {}
            tags: dict[str, str] = {}

            @classmethod
            def from_dict(cls, data):
                return cls()

            def inspect(self, since=None, until=None, limit=None, access=None):
                return []

            def quality(self, objects=None, since=None, until=None, limit=None, access=None):
                pass

            def export(self):
                return {}

            def describe(self):
                return {}

        instance = ConcreteAsset()
        assert isinstance(instance, IAssetLike)

    def test_protocol_missing_method_fails_check(self):
        """Test that missing protocol methods fail instance check."""

        class IncompleteAsset:
            glob: str = "/path/**/*.parquet"
            name: str | None = "test"
            filesystem: AssetFilesystem = AssetFilesystem.LOCAL
            objectkind: AssetObjectkind = AssetObjectkind.PARQUET
            partitions: list[str] | None = []
            description: str | None = "test description"
            owner: str | None = "test_owner"
            metadata: dict[str, any] = {}
            tags: dict[str, str] = {}
            # Missing from_dict, inspect, quality, export, describe

        instance = IncompleteAsset()
        assert not isinstance(instance, IAssetLike)

    def test_protocol_has_required_attributes(self):
        """Test that protocol requires glob, name, filesystem, objectkind, etc."""
        from assetlake.control.asset.local import LocalAsset

        asset = LocalAsset(
            glob="/path/**/*.parquet",
            name="test",
            tags={"env": "test"},
        )

        assert hasattr(asset, "glob")
        assert hasattr(asset, "name")
        assert hasattr(asset, "filesystem")
        assert hasattr(asset, "objectkind")
        assert hasattr(asset, "partitions")
        assert hasattr(asset, "description")
        assert hasattr(asset, "owner")
        assert hasattr(asset, "metadata")
        assert hasattr(asset, "tags")

    def test_protocol_has_required_methods(self):
        """Test that protocol requires from_dict, inspect, quality, export, describe."""
        from assetlake.control.asset.local import LocalAsset

        assert hasattr(LocalAsset, "from_dict")
        assert hasattr(LocalAsset, "inspect")
        assert hasattr(LocalAsset, "quality")
        assert hasattr(LocalAsset, "export")
        assert hasattr(LocalAsset, "describe")
