"""Unit tests for S3AssetObject."""

from __future__ import annotations

from datetime import datetime, timezone

from assetlake.control.asset.s3.object import S3AssetObject
from assetlake.domain.asset.filesystem import AssetFilesystem


class TestS3AssetObjectCreation:
    """Test S3AssetObject instantiation and basic attributes."""

    def test_create_minimal_object(self):
        """Test creating object with minimal required fields."""
        obj = S3AssetObject(uri="s3://my-bucket/data/file.parquet")

        assert obj.uri == "s3://my-bucket/data/file.parquet"
        assert obj.filesystem == AssetFilesystem.S3
        assert obj.size is None
        assert obj.modified_at is None

    def test_create_full_object(self):
        """Test creating object with all fields."""
        modified = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        metadata = {"StorageClass": "STANDARD", "ContentType": "application/octet-stream"}

        obj = S3AssetObject(
            uri="s3://test-bucket/data/test.parquet",
            size=1024,
            modified_at=modified,
            metadata=metadata,
        )

        assert obj.uri == "s3://test-bucket/data/test.parquet"
        assert obj.size == 1024
        assert obj.modified_at is not None
        assert obj.metadata == metadata

    def test_filesystem_is_always_s3(self):
        """Test that filesystem is always set to S3."""
        obj = S3AssetObject(uri="s3://bucket/data/file.csv")
        assert obj.filesystem == AssetFilesystem.S3


class TestS3AssetObjectURIFormats:
    """Test different S3 URI formats."""

    def test_standard_s3_uri(self):
        """Test standard s3:// URI format."""
        obj = S3AssetObject(uri="s3://my-bucket/path/to/file.parquet")
        assert obj.uri == "s3://my-bucket/path/to/file.parquet"

    def test_uri_with_nested_path(self):
        """Test URI with deeply nested path."""
        obj = S3AssetObject(uri="s3://warehouse/data/year=2024/month=03/day=15/file.parquet")
        assert obj.uri == "s3://warehouse/data/year=2024/month=03/day=15/file.parquet"

    def test_uri_with_special_characters(self):
        """Test URI with special characters in path."""
        obj = S3AssetObject(uri="s3://bucket/data-folder/file_name-123.parquet")
        assert obj.uri == "s3://bucket/data-folder/file_name-123.parquet"

    def test_uri_with_complex_bucket_name(self):
        """Test URI with complex bucket name."""
        obj = S3AssetObject(uri="s3://my-data-warehouse-prod/analytics/file.csv")
        assert obj.uri == "s3://my-data-warehouse-prod/analytics/file.csv"


class TestS3AssetObjectPartitionInference:
    """Test automatic partition extraction from URI."""

    def test_partitions_extracted_from_uri(self):
        """Test that partitions are auto-extracted from path with key=value."""
        obj = S3AssetObject(uri="s3://bucket/data/year=2024/month=03/file.parquet")
        assert obj.partitions == {"year": "2024", "month": "03"}

    def test_partitions_multiple_levels(self):
        """Test partition extraction with multiple levels."""
        obj = S3AssetObject(
            uri="s3://warehouse/data/year=2024/month=03/day=15/region=us-east-1/file.parquet"
        )
        assert obj.partitions == {
            "year": "2024",
            "month": "03",
            "day": "15",
            "region": "us-east-1",
        }

    def test_no_partitions_in_simple_path(self):
        """Test that empty partitions dict is returned for non-partitioned paths."""
        obj = S3AssetObject(uri="s3://bucket/data/simple/file.parquet")
        assert obj.partitions == {}

    def test_partitions_ignores_non_partition_dirs(self):
        """Test that directories without = are not treated as partitions."""
        obj = S3AssetObject(uri="s3://bucket/folder/year=2024/subfolder/file.parquet")
        assert obj.partitions == {"year": "2024"}
        assert "folder" not in obj.partitions
        assert "subfolder" not in obj.partitions

    def test_partitions_with_underscore_in_key(self):
        """Test partition extraction with underscores in key names."""
        obj = S3AssetObject(
            uri="s3://bucket/data/data_source=clickstream/event_type=page_view/file.json"
        )
        assert obj.partitions == {
            "data_source": "clickstream",
            "event_type": "page_view",
        }


class TestS3AssetObjectSerialization:
    """Test from_dict, export, and describe methods."""

    def test_from_dict_minimal(self):
        """Test creating object from minimal dict."""
        data = {"uri": "s3://bucket/data/file.parquet"}
        obj = S3AssetObject.from_dict(data)

        assert obj.uri == "s3://bucket/data/file.parquet"
        assert obj.filesystem == AssetFilesystem.S3

    def test_from_dict_with_all_fields(self):
        """Test creating object from complete dict."""
        data = {
            "uri": "s3://bucket/year=2024/file.parquet",
            "size": 2048,
            "modified_at": "2024-03-15T10:30:00+00:00",
            "metadata": {"StorageClass": "STANDARD"},
        }
        obj = S3AssetObject.from_dict(data)

        assert obj.uri == "s3://bucket/year=2024/file.parquet"
        assert obj.size == 2048
        assert obj.metadata == {"StorageClass": "STANDARD"}
        assert obj.partitions == {"year": "2024"}

    def test_export_returns_dict(self):
        """Test that export returns a dictionary."""
        obj = S3AssetObject(
            uri="s3://bucket/data/test.csv",
            size=512,
        )
        exported = obj.export()

        assert isinstance(exported, dict)
        assert exported["uri"] == "s3://bucket/data/test.csv"
        assert exported["size"] == 512
        assert exported["filesystem"] == AssetFilesystem.S3

    def test_describe_returns_string(self):
        """Test that describe returns a JSON string."""
        obj = S3AssetObject(uri="s3://bucket/data/file.parquet")
        description = obj.describe()

        assert isinstance(description, str)
        assert "s3://bucket/data/file.parquet" in description

    def test_roundtrip_from_dict_to_export(self):
        """Test that object can be serialized and deserialized."""
        original = S3AssetObject(
            uri="s3://bucket/year=2024/month=03/file.parquet",
            size=4096,
        )
        exported = original.export()
        restored = S3AssetObject.from_dict(exported)

        assert restored.uri == original.uri
        assert restored.size == original.size
        assert restored.partitions == original.partitions
