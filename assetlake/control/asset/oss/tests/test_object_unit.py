"""Unit tests for OSSAssetObject."""

from __future__ import annotations

from datetime import datetime, timezone

from assetlake.control.asset.oss.object import OSSAssetObject
from assetlake.domain.asset.filesystem import AssetFilesystem


class TestOSSAssetObjectCreation:
    """Test OSSAssetObject instantiation and basic attributes."""

    def test_create_minimal_object(self):
        """Test creating object with minimal required fields."""
        obj = OSSAssetObject(uri="oss://my-bucket/data/file.parquet")

        assert obj.uri == "oss://my-bucket/data/file.parquet"
        assert obj.filesystem == AssetFilesystem.OSS
        assert obj.size is None
        assert obj.modified_at is None

    def test_create_full_object(self):
        """Test creating object with all fields."""
        modified = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        metadata = {"storage_class": "Standard", "content_type": "application/octet-stream"}

        obj = OSSAssetObject(
            uri="oss://test-bucket/data/test.parquet",
            size=1024,
            modified_at=modified,
            metadata=metadata,
        )

        assert obj.uri == "oss://test-bucket/data/test.parquet"
        assert obj.size == 1024
        assert obj.modified_at is not None
        assert obj.metadata == metadata

    def test_filesystem_is_always_oss(self):
        """Test that filesystem is always set to OSS."""
        obj = OSSAssetObject(uri="oss://bucket/data/file.csv")
        assert obj.filesystem == AssetFilesystem.OSS


class TestOSSAssetObjectURIFormats:
    """Test different OSS URI formats."""

    def test_standard_oss_uri(self):
        """Test standard oss:// URI format."""
        obj = OSSAssetObject(uri="oss://my-bucket/path/to/file.parquet")
        assert obj.uri == "oss://my-bucket/path/to/file.parquet"

    def test_uri_with_nested_path(self):
        """Test URI with deeply nested path."""
        obj = OSSAssetObject(uri="oss://warehouse/data/year=2024/month=03/day=15/file.parquet")
        assert obj.uri == "oss://warehouse/data/year=2024/month=03/day=15/file.parquet"

    def test_uri_with_special_characters(self):
        """Test URI with special characters in path."""
        obj = OSSAssetObject(uri="oss://bucket/data-folder/file_name-123.parquet")
        assert obj.uri == "oss://bucket/data-folder/file_name-123.parquet"

    def test_uri_with_complex_bucket_name(self):
        """Test URI with complex bucket name."""
        obj = OSSAssetObject(uri="oss://my-data-warehouse-prod/analytics/file.csv")
        assert obj.uri == "oss://my-data-warehouse-prod/analytics/file.csv"


class TestOSSAssetObjectPartitionInference:
    """Test automatic partition extraction from URI."""

    def test_partitions_extracted_from_uri(self):
        """Test that partitions are auto-extracted from path with key=value."""
        obj = OSSAssetObject(uri="oss://bucket/data/year=2024/month=03/file.parquet")

        assert obj.partitions == {"year": "2024", "month": "03"}

    def test_partitions_multiple_levels(self):
        """Test partition extraction with multiple levels."""
        obj = OSSAssetObject(
            uri="oss://warehouse/data/year=2024/month=03/day=15/region=us-west/file.parquet"
        )

        assert obj.partitions == {
            "year": "2024",
            "month": "03",
            "day": "15",
            "region": "us-west",
        }

    def test_partitions_with_complex_values(self):
        """Test partition extraction with special characters in values."""
        obj = OSSAssetObject(uri="oss://bucket/region=cn-hangzhou/category=tech_hardware/file.csv")

        assert obj.partitions == {
            "region": "cn-hangzhou",
            "category": "tech_hardware",
        }

    def test_no_partitions_in_simple_path(self):
        """Test that empty partitions dict is returned for non-partitioned paths."""
        obj = OSSAssetObject(uri="oss://bucket/data/simple/file.parquet")
        assert obj.partitions == {}

    def test_partitions_ignores_non_partition_dirs(self):
        """Test that directories without = are not treated as partitions."""
        obj = OSSAssetObject(uri="oss://bucket/folder/year=2024/subfolder/file.parquet")

        assert obj.partitions == {"year": "2024"}
        assert "folder" not in obj.partitions
        assert "subfolder" not in obj.partitions

    def test_partitions_with_underscore_in_key(self):
        """Test partition extraction with underscores in key names."""
        obj = OSSAssetObject(
            uri="oss://bucket/data/data_source=clickstream/event_type=page_view/file.json"
        )

        assert obj.partitions == {
            "data_source": "clickstream",
            "event_type": "page_view",
        }


class TestOSSAssetObjectSerialization:
    """Test from_dict, export, and describe methods."""

    def test_from_dict_minimal(self):
        """Test creating object from minimal dict."""
        data = {"uri": "oss://bucket/data/file.parquet"}
        obj = OSSAssetObject.from_dict(data)

        assert obj.uri == "oss://bucket/data/file.parquet"
        assert obj.filesystem == AssetFilesystem.OSS

    def test_from_dict_with_all_fields(self):
        """Test creating object from complete dict."""
        data = {
            "uri": "oss://bucket/year=2024/file.parquet",
            "size": 2048,
            "modified_at": "2024-03-15T10:30:00+00:00",
            "metadata": {"storage_class": "Standard"},
        }
        obj = OSSAssetObject.from_dict(data)

        assert obj.uri == "oss://bucket/year=2024/file.parquet"
        assert obj.size == 2048
        assert obj.metadata == {"storage_class": "Standard"}
        assert obj.partitions == {"year": "2024"}

    def test_export_returns_dict(self):
        """Test that export returns a dictionary."""
        obj = OSSAssetObject(
            uri="oss://bucket/data/test.csv",
            size=512,
        )
        exported = obj.export()

        assert isinstance(exported, dict)
        assert exported["uri"] == "oss://bucket/data/test.csv"
        assert exported["size"] == 512
        assert exported["filesystem"] == AssetFilesystem.OSS

    def test_describe_returns_string(self):
        """Test that describe returns a JSON string."""
        obj = OSSAssetObject(uri="oss://bucket/data/file.parquet")
        description = obj.describe()

        assert isinstance(description, str)
        assert "oss://bucket/data/file.parquet" in description

    def test_roundtrip_from_dict_to_export(self):
        """Test that object can be serialized and deserialized."""
        original = OSSAssetObject(
            uri="oss://bucket/year=2024/month=03/file.parquet",
            size=4096,
        )
        exported = original.export()
        restored = OSSAssetObject.from_dict(exported)

        assert restored.uri == original.uri
        assert restored.size == original.size
        assert restored.partitions == original.partitions


class TestOSSAssetObjectSizeHandling:
    """Test object size attribute."""

    def test_zero_size(self):
        """Test object with zero size."""
        obj = OSSAssetObject(
            uri="oss://bucket/empty.txt",
            size=0,
        )
        assert obj.size == 0

    def test_large_size(self):
        """Test object with large size."""
        large_size = 10 * 1024 * 1024 * 1024  # 10 GB
        obj = OSSAssetObject(
            uri="oss://bucket/large-file.parquet",
            size=large_size,
        )
        assert obj.size == large_size

    def test_none_size(self):
        """Test object with None size."""
        obj = OSSAssetObject(uri="oss://bucket/file.csv")
        assert obj.size is None


class TestOSSAssetObjectTimestamps:
    """Test object timestamp handling."""

    def test_modified_at_with_timezone(self):
        """Test modified_at with timezone aware datetime."""
        modified = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        obj = OSSAssetObject(
            uri="oss://bucket/file.parquet",
            modified_at=modified,
        )
        assert obj.modified_at is not None
        assert obj.modified_at.tzinfo is not None

    def test_none_timestamp(self):
        """Test object with None timestamp."""
        obj = OSSAssetObject(uri="oss://bucket/file.parquet")
        assert obj.modified_at is None

    def test_modified_at_from_string(self):
        """Test modified_at can be set from ISO format string."""
        obj = OSSAssetObject(
            uri="oss://bucket/file.parquet",
            modified_at="2024-03-15T10:30:00+00:00",
        )
        assert obj.modified_at is not None
        assert obj.modified_at.year == 2024
        assert obj.modified_at.month == 3
        assert obj.modified_at.day == 15


class TestOSSAssetObjectMetadata:
    """Test object metadata handling."""

    def test_empty_metadata(self):
        """Test object with empty metadata dict."""
        obj = OSSAssetObject(
            uri="oss://bucket/file.parquet",
            metadata={},
        )
        assert obj.metadata == {}

    def test_metadata_with_storage_class(self):
        """Test metadata with OSS storage class."""
        obj = OSSAssetObject(
            uri="oss://bucket/file.parquet",
            metadata={"storage_class": "Archive"},
        )
        assert obj.metadata["storage_class"] == "Archive"

    def test_metadata_with_content_type(self):
        """Test metadata with content type."""
        obj = OSSAssetObject(
            uri="oss://bucket/file.csv",
            metadata={"content_type": "text/csv"},
        )
        assert obj.metadata["content_type"] == "text/csv"

    def test_metadata_with_multiple_fields(self):
        """Test metadata with multiple custom fields."""
        metadata = {
            "storage_class": "Standard",
            "content_type": "application/octet-stream",
            "etag": "abc123def456",
            "server_side_encryption": "AES256",
        }
        obj = OSSAssetObject(
            uri="oss://bucket/file.parquet",
            metadata=metadata,
        )
        assert obj.metadata == metadata

    def test_none_metadata_defaults_to_empty_dict(self):
        """Test object with no metadata defaults to empty dict."""
        obj = OSSAssetObject(uri="oss://bucket/file.parquet")
        assert obj.metadata == {}


class TestOSSAssetObjectEdgeCases:
    """Test edge cases and error handling."""

    def test_uri_with_trailing_slash(self):
        """Test URI with trailing slash (directory-like)."""
        obj = OSSAssetObject(uri="oss://bucket/data/")
        assert obj.uri == "oss://bucket/data/"

    def test_uri_with_various_characters(self):
        """Test that URI can contain various characters."""
        obj = OSSAssetObject(uri="oss://bucket/data/file.parquet")
        assert obj.uri == "oss://bucket/data/file.parquet"

    def test_minimal_uri_format(self):
        """Test minimal valid URI format."""
        obj = OSSAssetObject(uri="oss://bucket/file")
        assert obj.uri == "oss://bucket/file"


class TestOSSAssetObjectBucketExtraction:
    """Test bucket name extraction from URI."""

    def test_bucket_in_uri_simple(self):
        """Test extracting simple bucket name."""
        obj = OSSAssetObject(uri="oss://my-bucket/file.parquet")
        assert "my-bucket" in obj.uri

    def test_bucket_in_uri_complex(self):
        """Test extracting bucket name with dashes and numbers."""
        obj = OSSAssetObject(uri="oss://data-warehouse-2024/file.csv")
        assert "data-warehouse-2024" in obj.uri

    def test_bucket_from_nested_path(self):
        """Test that bucket is always the first component after oss://."""
        obj = OSSAssetObject(uri="oss://prod-bucket/year=2024/month=03/file.parquet")
        assert "prod-bucket" in obj.uri


class TestOSSAssetObjectComparison:
    """Test object comparison and identity."""

    def test_objects_with_same_uri_have_same_uri(self):
        """Test that objects with same URI have same URI attribute."""
        obj1 = OSSAssetObject(uri="oss://bucket/file.parquet", size=100)
        obj2 = OSSAssetObject(uri="oss://bucket/file.parquet", size=200)
        assert obj1.uri == obj2.uri

    def test_objects_are_different_instances(self):
        """Test that different objects are different instances."""
        obj1 = OSSAssetObject(uri="oss://bucket/file.parquet")
        obj2 = OSSAssetObject(uri="oss://bucket/file.parquet")
        assert obj1 is not obj2
