"""Unit tests for LocalAssetObject."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from assetlake.control.asset.local.object import LocalAssetObject
from assetlake.domain.asset.filesystem import AssetFilesystem


class TestLocalAssetObjectCreation:
    """Test LocalAssetObject instantiation and basic attributes."""

    def test_create_minimal_object(self):
        """Test creating object with minimal required fields."""
        obj = LocalAssetObject(uri="/data/file.parquet")

        assert obj.uri == "/data/file.parquet"
        assert obj.filesystem == AssetFilesystem.LOCAL
        assert obj.size is None
        assert obj.modified_at is None
        assert obj.type is None
        assert obj.created_at is None

    def test_create_full_object(self):
        """Test creating object with all fields."""
        modified = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        created = datetime(2024, 3, 1, 8, 0, 0, tzinfo=timezone.utc)
        metadata = {"uid": 1000, "gid": 1000, "mode": 0o644}

        obj = LocalAssetObject(
            uri="/data/test.parquet",
            size=1024,
            modified_at=modified,
            created_at=created,
            type="file",
            metadata=metadata,
        )

        assert obj.uri == "/data/test.parquet"
        assert obj.size == 1024
        assert obj.modified_at == modified
        assert obj.created_at == created
        assert obj.type == "file"
        assert obj.metadata == metadata

    def test_filesystem_is_always_local(self):
        """Test that filesystem is always set to LOCAL."""
        obj = LocalAssetObject(uri="/data/file.csv")
        assert obj.filesystem == AssetFilesystem.LOCAL


class TestLocalAssetObjectPathProperty:
    """Test the computed path property."""

    def test_path_from_simple_uri(self, tmp_path: Path):
        """Test path extraction from simple URI."""
        test_file = tmp_path / "file.parquet"
        obj = LocalAssetObject(uri=str(test_file))
        assert obj.path == test_file

    def test_path_from_file_uri_scheme(self, tmp_path: Path):
        """Test path extraction from file:// URI."""
        test_file = tmp_path / "file.parquet"
        obj = LocalAssetObject(uri=f"file://{test_file}")
        assert "file://" not in str(obj.path)
        assert obj.path == test_file

    def test_path_with_tilde_expansion(self):
        """Test that path expands ~ to home directory."""
        obj = LocalAssetObject(uri="~/data/file.csv")
        assert "~" not in str(obj.path)
        assert obj.path.is_absolute()

    def test_path_resolves_to_absolute(self):
        """Test that path is resolved to absolute."""
        obj = LocalAssetObject(uri="./data/file.parquet")
        assert obj.path.is_absolute()


class TestLocalAssetObjectPartitionInference:
    """Test automatic partition extraction from URI."""

    def test_partitions_extracted_from_uri(self):
        """Test that partitions are auto-extracted from path with key=value."""
        obj = LocalAssetObject(uri="/data/year=2024/month=03/file.parquet")

        assert obj.partitions == {"year": "2024", "month": "03"}

    def test_partitions_multiple_levels(self):
        """Test partition extraction with multiple levels."""
        obj = LocalAssetObject(
            uri="/warehouse/year=2024/month=03/day=15/region=us-west/file.parquet"
        )

        assert obj.partitions == {
            "year": "2024",
            "month": "03",
            "day": "15",
            "region": "us-west",
        }

    def test_partitions_with_complex_values(self):
        """Test partition extraction with special characters in values."""
        obj = LocalAssetObject(uri="/data/region=us-west-1/category=tech_hardware/file.csv")

        assert obj.partitions == {
            "region": "us-west-1",
            "category": "tech_hardware",
        }

    def test_no_partitions_in_simple_path(self):
        """Test that empty partitions dict is returned for non-partitioned paths."""
        obj = LocalAssetObject(uri="/data/simple/file.parquet")
        assert obj.partitions == {}

    def test_partitions_ignores_non_partition_dirs(self):
        """Test that directories without = are not treated as partitions."""
        obj = LocalAssetObject(uri="/data/folder/year=2024/subfolder/file.parquet")

        assert obj.partitions == {"year": "2024"}
        assert "folder" not in obj.partitions
        assert "subfolder" not in obj.partitions


class TestLocalAssetObjectSerialization:
    """Test from_dict, export, and describe methods."""

    def test_from_dict_minimal(self):
        """Test creating object from minimal dict."""
        data = {"uri": "/data/file.parquet"}
        obj = LocalAssetObject.from_dict(data)

        assert obj.uri == "/data/file.parquet"
        assert obj.filesystem == AssetFilesystem.LOCAL

    def test_from_dict_with_all_fields(self):
        """Test creating object from complete dict."""
        data = {
            "uri": "/data/year=2024/file.parquet",
            "size": 2048,
            "modified_at": "2024-03-15T10:30:00+00:00",
            "created_at": "2024-03-01T08:00:00+00:00",
            "type": "file",
            "metadata": {"uid": 1000},
        }
        obj = LocalAssetObject.from_dict(data)

        assert obj.uri == "/data/year=2024/file.parquet"
        assert obj.size == 2048
        assert obj.type == "file"
        assert obj.metadata == {"uid": 1000}
        assert obj.partitions == {"year": "2024"}

    def test_export_returns_dict(self):
        """Test that export returns a dictionary."""
        obj = LocalAssetObject(
            uri="/data/test.csv",
            size=512,
            type="file",
        )
        exported = obj.export()

        assert isinstance(exported, dict)
        assert exported["uri"] == "/data/test.csv"
        assert exported["size"] == 512
        assert exported["filesystem"] == AssetFilesystem.LOCAL

    def test_describe_returns_string(self):
        """Test that describe returns a JSON string."""
        obj = LocalAssetObject(uri="/data/file.parquet")
        description = obj.describe()

        assert isinstance(description, str)
        assert "/data/file.parquet" in description

    def test_roundtrip_from_dict_to_export(self):
        """Test that object can be serialized and deserialized."""
        original = LocalAssetObject(
            uri="/data/year=2024/month=03/file.parquet",
            size=4096,
            type="file",
        )
        exported = original.export()
        restored = LocalAssetObject.from_dict(exported)

        assert restored.uri == original.uri
        assert restored.size == original.size
        assert restored.type == original.type
        assert restored.partitions == original.partitions


class TestLocalAssetObjectEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_uri_creates_object(self):
        """Test that empty URI is allowed (may fail on path resolution)."""
        obj = LocalAssetObject(uri="")
        assert obj.uri == ""

    def test_windows_style_path(self):
        """Test handling of Windows-style paths."""
        obj = LocalAssetObject(uri="C:/data/file.parquet")
        assert obj.uri == "C:/data/file.parquet"

    def test_null_modified_at(self):
        """Test that None modified_at is handled."""
        obj = LocalAssetObject(uri="/data/file.parquet", modified_at=None)
        assert obj.modified_at is None

    def test_zero_size_file(self):
        """Test that zero size is handled correctly."""
        obj = LocalAssetObject(uri="/data/empty.txt", size=0)
        assert obj.size == 0

    def test_metadata_with_nested_dict(self):
        """Test metadata can contain nested structures."""
        metadata = {
            "stats": {"lines": 1000, "bytes": 5000},
            "flags": ["compressed", "validated"],
        }
        obj = LocalAssetObject(uri="/data/file.parquet", metadata=metadata)
        assert obj.metadata == metadata
