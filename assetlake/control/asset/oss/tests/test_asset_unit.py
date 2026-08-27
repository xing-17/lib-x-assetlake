"""Unit tests for OSSAsset."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import Mock, patch

from assetlake.control.asset.oss.asset import OSSAsset, OSSAssetDomain
from assetlake.control.asset.oss.object import OSSAssetObject
from assetlake.domain.asset.filesystem import AssetFilesystem
from assetlake.domain.asset.objectkind import AssetObjectkind


class TestOSSAssetDomain:
    """Test OSSAssetDomain model."""

    def test_filesystem_defaults_to_oss(self):
        """Test that filesystem is always OSS."""
        domain = OSSAssetDomain(
            glob="oss://my-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )
        assert domain.filesystem == AssetFilesystem.OSS

    def test_create_with_all_fields(self):
        """Test creating domain with all fields."""
        domain = OSSAssetDomain(
            glob="oss://test-bucket/warehouse/**/*.csv",
            region="cn-shanghai",
            internal=True,
            name="test_asset",
            objectkind=AssetObjectkind.CSV,
            partitions=["year", "month"],
            description="Test asset",
            owner="data_team",
            metadata={"source": "test"},
            tags={"env": "dev"},
        )

        assert domain.glob == "oss://test-bucket/warehouse/**/*.csv"
        assert domain.region == "cn-shanghai"
        assert domain.internal is True
        assert domain.name == "test_asset"
        assert domain.objectkind == AssetObjectkind.CSV
        assert domain.partitions == ["year", "month"]
        assert domain.description == "Test asset"
        assert domain.owner == "data_team"
        assert domain.metadata == {"source": "test"}
        assert domain.tags == {"env": "dev"}

    def test_bucket_extraction(self):
        """Test bucket property extracts bucket name from glob."""
        domain = OSSAssetDomain(
            glob="oss://my-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )
        assert domain.bucket == "my-bucket"

    def test_common_prefix_extraction(self):
        """Test common_prefix property extracts prefix from glob."""
        domain = OSSAssetDomain(
            glob="oss://my-bucket/data/warehouse/**/*.parquet",
            region="cn-hangzhou",
        )
        assert domain.common_prefix == "data/warehouse/"

    def test_object_pattern_extraction(self):
        """Test object_pattern property extracts pattern from glob."""
        domain = OSSAssetDomain(
            glob="oss://my-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )
        assert domain.object_pattern == "**/*.parquet"

    def test_endpoint_external(self):
        """Test endpoint generation for external access."""
        domain = OSSAssetDomain(
            glob="oss://my-bucket/data/**/*.parquet",
            region="cn-hangzhou",
            internal=False,
        )
        assert domain.endpoint == "oss-cn-hangzhou.aliyuncs.com"

    def test_endpoint_internal(self):
        """Test endpoint generation for internal access."""
        domain = OSSAssetDomain(
            glob="oss://my-bucket/data/**/*.parquet",
            region="cn-beijing",
            internal=True,
        )
        assert domain.endpoint == "oss-cn-beijing-internal.aliyuncs.com"


class TestOSSAssetCreation:
    """Test OSSAsset instantiation."""

    def test_create_minimal_asset(self):
        """Test creating asset with minimal required fields."""
        asset = OSSAsset(
            glob="oss://my-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        assert asset.glob == "oss://my-bucket/data/**/*.parquet"
        assert asset.region == "cn-hangzhou"
        assert asset.filesystem == AssetFilesystem.OSS
        assert asset.name is None
        assert asset.partitions == []

    def test_create_full_asset(self):
        """Test creating asset with all fields."""
        asset = OSSAsset(
            glob="oss://warehouse-bucket/year=*/month=*/*.parquet",
            region="cn-shanghai",
            name="sales_data",
            objectkind=AssetObjectkind.PARQUET,
            partitions=["year", "month"],
            description="Sales transaction data",
            owner="analytics_team",
            metadata={"format": "parquet", "compression": "snappy"},
            tags={"category": "sales", "env": "prod"},
        )

        assert asset.glob == "oss://warehouse-bucket/year=*/month=*/*.parquet"
        assert asset.region == "cn-shanghai"
        assert asset.name == "sales_data"
        assert asset.objectkind == AssetObjectkind.PARQUET
        assert asset.partitions == ["year", "month"]
        assert asset.description == "Sales transaction data"
        assert asset.owner == "analytics_team"
        assert asset.metadata == {"format": "parquet", "compression": "snappy"}
        assert asset.tags == {"category": "sales", "env": "prod"}

    def test_domain_class_is_set(self):
        """Test that _domain_class is properly set."""
        assert OSSAsset._domain_class is OSSAssetDomain

    def test_domain_attribute_accessible(self):
        """Test that domain attribute is accessible through __getattr__."""
        asset = OSSAsset(
            glob="oss://my-bucket/data/*.csv",
            region="cn-hangzhou",
            name="test",
        )
        assert hasattr(asset, "domain")
        assert isinstance(asset.domain, OSSAssetDomain)

    def test_bucket_property_through_domain(self):
        """Test accessing bucket through domain."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )
        assert asset.domain.bucket == "test-bucket"

    def test_endpoint_property_through_domain(self):
        """Test accessing endpoint through domain."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )
        assert asset.domain.endpoint == "oss-cn-hangzhou.aliyuncs.com"


class TestOSSAssetRegions:
    """Test OSS asset with different regions."""

    def test_hangzhou_region(self):
        """Test asset with Hangzhou region."""
        asset = OSSAsset(
            glob="oss://bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )
        assert asset.region == "cn-hangzhou"
        assert asset.domain.endpoint == "oss-cn-hangzhou.aliyuncs.com"

    def test_shanghai_region(self):
        """Test asset with Shanghai region."""
        asset = OSSAsset(
            glob="oss://bucket/data/**/*.parquet",
            region="cn-shanghai",
        )
        assert asset.region == "cn-shanghai"
        assert asset.domain.endpoint == "oss-cn-shanghai.aliyuncs.com"

    def test_beijing_region(self):
        """Test asset with Beijing region."""
        asset = OSSAsset(
            glob="oss://bucket/data/**/*.parquet",
            region="cn-beijing",
        )
        assert asset.region == "cn-beijing"
        assert asset.domain.endpoint == "oss-cn-beijing.aliyuncs.com"

    def test_shenzhen_region(self):
        """Test asset with Shenzhen region."""
        asset = OSSAsset(
            glob="oss://bucket/data/**/*.parquet",
            region="cn-shenzhen",
        )
        assert asset.region == "cn-shenzhen"
        assert asset.domain.endpoint == "oss-cn-shenzhen.aliyuncs.com"


class TestOSSAssetInternalEndpoint:
    """Test internal vs external endpoint configuration."""

    def test_external_endpoint_default(self):
        """Test that external endpoint is used by default."""
        asset = OSSAsset(
            glob="oss://bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )
        assert asset.domain.internal is False
        assert "internal" not in asset.domain.endpoint

    def test_internal_endpoint_explicit(self):
        """Test explicitly setting internal endpoint."""
        domain = OSSAssetDomain(
            glob="oss://bucket/data/**/*.parquet",
            region="cn-hangzhou",
            internal=True,
        )
        assert domain.internal is True
        assert "internal" in domain.endpoint
        assert domain.endpoint == "oss-cn-hangzhou-internal.aliyuncs.com"


class TestOSSAssetObjectKinds:
    """Test OSS asset with different object kinds."""

    def test_parquet_objectkind(self):
        """Test asset with PARQUET objectkind."""
        asset = OSSAsset(
            glob="oss://bucket/data/**/*.parquet",
            region="cn-hangzhou",
            objectkind=AssetObjectkind.PARQUET,
        )
        assert asset.objectkind == AssetObjectkind.PARQUET

    def test_csv_objectkind(self):
        """Test asset with CSV objectkind."""
        asset = OSSAsset(
            glob="oss://bucket/data/**/*.csv",
            region="cn-hangzhou",
            objectkind=AssetObjectkind.CSV,
        )
        assert asset.objectkind == AssetObjectkind.CSV

    def test_csv_objectkind_variant(self):
        """Test asset with CSV objectkind variant."""
        asset = OSSAsset(
            glob="oss://bucket/data/**/*.csv",
            region="cn-hangzhou",
            objectkind=AssetObjectkind.CSV,
        )
        assert asset.objectkind == AssetObjectkind.CSV

    def test_object_objectkind(self):
        """Test asset with generic OBJECT objectkind."""
        asset = OSSAsset(
            glob="oss://bucket/data/**/*",
            region="cn-hangzhou",
            objectkind=AssetObjectkind.OBJECT,
        )
        assert asset.objectkind == AssetObjectkind.OBJECT


class TestOSSAssetPartitions:
    """Test OSS asset partition handling."""

    def test_single_partition(self):
        """Test asset with single partition."""
        asset = OSSAsset(
            glob="oss://bucket/year=*/*.parquet",
            region="cn-hangzhou",
            partitions=["year"],
        )
        assert asset.partitions == ["year"]

    def test_multiple_partitions(self):
        """Test asset with multiple partitions."""
        asset = OSSAsset(
            glob="oss://bucket/year=*/month=*/day=*/*.parquet",
            region="cn-hangzhou",
            partitions=["year", "month", "day"],
        )
        assert asset.partitions == ["year", "month", "day"]

    def test_no_partitions(self):
        """Test asset without partitions."""
        asset = OSSAsset(
            glob="oss://bucket/data/*.parquet",
            region="cn-hangzhou",
        )
        assert asset.partitions == []

    def test_partitions_order_preserved(self):
        """Test that partition order is preserved."""
        asset = OSSAsset(
            glob="oss://bucket/region=*/year=*/month=*/*.parquet",
            region="cn-hangzhou",
            partitions=["region", "year", "month"],
        )
        assert asset.partitions == ["region", "year", "month"]


class TestOSSAssetInspect:
    """Comprehensive tests for OSSAsset.inspect() method."""

    def _create_mock_oss_object(self, key: str, size: int, last_modified: datetime) -> Mock:
        """Helper to create a mock OSS object."""
        mock_obj = Mock()
        mock_obj.key = key
        mock_obj.size = size
        mock_obj.last_modified = last_modified
        return mock_obj

    def _create_mock_page(self, objects: list) -> Mock:
        """Helper to create a mock page with OSS objects."""
        mock_page = Mock()
        mock_page.contents = objects
        return mock_page

    def test_inspect_basic_no_filters(self):
        """Test inspect returns all matching objects without filters."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        # Create mock objects with paths that match ** pattern (requires subdirectory)
        now = datetime.now(timezone.utc)
        mock_objects = [
            self._create_mock_oss_object("data/warehouse/file1.parquet", 1024, now),
            self._create_mock_oss_object("data/raw/file2.parquet", 2048, now),
            self._create_mock_oss_object("data/archive/subdir/file3.parquet", 3072, now),
        ]
        mock_page = self._create_mock_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect()

        assert len(results) == 3
        assert all(isinstance(obj, OSSAssetObject) for obj in results)
        assert results[0].uri == "oss://test-bucket/data/warehouse/file1.parquet"
        assert results[1].uri == "oss://test-bucket/data/raw/file2.parquet"
        assert results[2].uri == "oss://test-bucket/data/archive/subdir/file3.parquet"

    def test_inspect_since_filter(self):
        """Test inspect filters objects by since datetime."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        base_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        since_time = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)

        mock_objects = [
            self._create_mock_oss_object(
                "data/archive/old.parquet", 1024, base_time
            ),  # Before since
            self._create_mock_oss_object(
                "data/recent/new1.parquet",
                2048,
                datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            ),  # After since
            self._create_mock_oss_object(
                "data/latest/new2.parquet", 3072, datetime(2024, 1, 3, 0, 0, 0, tzinfo=timezone.utc)
            ),  # After since
        ]
        mock_page = self._create_mock_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect(since=since_time)

        assert len(results) == 2
        assert all(obj.modified_at >= since_time for obj in results if obj.modified_at)
        assert "old.parquet" not in [obj.uri for obj in results]

    def test_inspect_until_filter(self):
        """Test inspect filters objects by until datetime."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        until_time = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)

        mock_objects = [
            self._create_mock_oss_object(
                "data/archive/old1.parquet",
                1024,
                datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            ),  # Before until
            self._create_mock_oss_object(
                "data/archive/old2.parquet",
                2048,
                datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),  # Before until
            self._create_mock_oss_object(
                "data/recent/new.parquet", 3072, datetime(2024, 1, 3, 0, 0, 0, tzinfo=timezone.utc)
            ),  # After until
        ]
        mock_page = self._create_mock_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect(until=until_time)

        assert len(results) == 2
        assert all(obj.modified_at <= until_time for obj in results if obj.modified_at)
        assert "new.parquet" not in [obj.uri for obj in results]

    def test_inspect_since_and_until_filter(self):
        """Test inspect filters objects with both since and until."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        since_time = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        until_time = datetime(2024, 1, 4, 0, 0, 0, tzinfo=timezone.utc)

        mock_objects = [
            self._create_mock_oss_object(
                "data/archive/too_old.parquet",
                1024,
                datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            ),  # Before since
            self._create_mock_oss_object(
                "data/recent/in_range1.parquet",
                2048,
                datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            ),  # In range
            self._create_mock_oss_object(
                "data/recent/in_range2.parquet",
                3072,
                datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
            ),  # In range
            self._create_mock_oss_object(
                "data/latest/too_new.parquet",
                4096,
                datetime(2024, 1, 5, 0, 0, 0, tzinfo=timezone.utc),
            ),  # After until
        ]
        mock_page = self._create_mock_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect(since=since_time, until=until_time)

        assert len(results) == 2
        assert all(
            since_time <= obj.modified_at <= until_time for obj in results if obj.modified_at
        )
        uris = [obj.uri for obj in results]
        assert "oss://test-bucket/data/recent/in_range1.parquet" in uris
        assert "oss://test-bucket/data/recent/in_range2.parquet" in uris

    def test_inspect_limit(self):
        """Test inspect respects the limit parameter."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        now = datetime.now(timezone.utc)
        mock_objects = [
            self._create_mock_oss_object(f"data/warehouse/file{i}.parquet", 1024 * i, now)
            for i in range(10)
        ]
        mock_page = self._create_mock_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect(limit=3)

        assert len(results) == 3

    def test_inspect_limit_one(self):
        """Test inspect with limit=1 returns only one result."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        now = datetime.now(timezone.utc)
        mock_objects = [
            self._create_mock_oss_object("data/warehouse/file1.parquet", 1024, now),
            self._create_mock_oss_object("data/warehouse/file2.parquet", 2048, now),
        ]
        mock_page = self._create_mock_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect(limit=1)

        assert len(results) == 1

    def test_inspect_glob_pattern_matching(self):
        """Test inspect filters objects by glob pattern."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        now = datetime.now(timezone.utc)
        mock_objects = [
            self._create_mock_oss_object("data/warehouse/file1.parquet", 1024, now),  # Matches
            self._create_mock_oss_object(
                "data/warehouse/file2.csv", 2048, now
            ),  # Does not match (wrong extension)
            self._create_mock_oss_object("data/archive/subdir/file3.parquet", 3072, now),  # Matches
            self._create_mock_oss_object(
                "other/warehouse/file4.parquet", 4096, now
            ),  # Does not match (wrong prefix)
        ]
        mock_page = self._create_mock_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect()

        # Should only return .parquet files under data/**
        assert len(results) == 2
        uris = [obj.uri for obj in results]
        assert "oss://test-bucket/data/warehouse/file1.parquet" in uris
        assert "oss://test-bucket/data/archive/subdir/file3.parquet" in uris

    def test_inspect_empty_results(self):
        """Test inspect with no matching objects returns empty list."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        # Empty page
        mock_page = self._create_mock_page([])

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect()

        assert len(results) == 0
        assert isinstance(results, list)

    def test_inspect_no_matching_glob(self):
        """Test inspect when no objects match the glob pattern."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        now = datetime.now(timezone.utc)
        # All objects are CSV files, but glob expects parquet
        mock_objects = [
            self._create_mock_oss_object("data/warehouse/file1.csv", 1024, now),
            self._create_mock_oss_object("data/archive/file2.csv", 2048, now),
        ]
        mock_page = self._create_mock_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect()

        assert len(results) == 0

    def test_inspect_results_sorted_by_modified_at_desc(self):
        """Test inspect returns results sorted by modified_at descending."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        # Create objects with different timestamps
        time1 = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        time2 = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        time3 = datetime(2024, 1, 3, 0, 0, 0, tzinfo=timezone.utc)

        mock_objects = [
            self._create_mock_oss_object("data/warehouse/file2.parquet", 2048, time2),  # Middle
            self._create_mock_oss_object("data/warehouse/file1.parquet", 1024, time1),  # Oldest
            self._create_mock_oss_object("data/warehouse/file3.parquet", 3072, time3),  # Newest
        ]
        mock_page = self._create_mock_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect()

        assert len(results) == 3
        # Results should be sorted by modified_at descending (newest first)
        assert results[0].uri == "oss://test-bucket/data/warehouse/file3.parquet"
        assert results[0].modified_at == time3
        assert results[1].uri == "oss://test-bucket/data/warehouse/file2.parquet"
        assert results[1].modified_at == time2
        assert results[2].uri == "oss://test-bucket/data/warehouse/file1.parquet"
        assert results[2].modified_at == time1

    def test_inspect_multiple_pages(self):
        """Test inspect handles multiple pages from iterator."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        now = datetime.now(timezone.utc)
        # Create multiple pages
        page1_objects = [
            self._create_mock_oss_object("data/warehouse/file1.parquet", 1024, now),
            self._create_mock_oss_object("data/warehouse/file2.parquet", 2048, now),
        ]
        page2_objects = [
            self._create_mock_oss_object("data/archive/file3.parquet", 3072, now),
            self._create_mock_oss_object("data/archive/file4.parquet", 4096, now),
        ]
        mock_page1 = self._create_mock_page(page1_objects)
        mock_page2 = self._create_mock_page(page2_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page1, mock_page2]):
            results = asset.inspect()

        assert len(results) == 4

    def test_inspect_limit_across_pages(self):
        """Test inspect limit works correctly across multiple pages."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        now = datetime.now(timezone.utc)
        # Create multiple pages
        page1_objects = [
            self._create_mock_oss_object("data/warehouse/file1.parquet", 1024, now),
            self._create_mock_oss_object("data/warehouse/file2.parquet", 2048, now),
        ]
        page2_objects = [
            self._create_mock_oss_object("data/archive/file3.parquet", 3072, now),
            self._create_mock_oss_object("data/archive/file4.parquet", 4096, now),
        ]
        mock_page1 = self._create_mock_page(page1_objects)
        mock_page2 = self._create_mock_page(page2_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page1, mock_page2]):
            results = asset.inspect(limit=3)

        assert len(results) == 3

    def test_inspect_object_attributes(self):
        """Test inspect creates OSSAssetObject with correct attributes."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        modified_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        mock_objects = [
            self._create_mock_oss_object("data/warehouse/file1.parquet", 12345, modified_time),
        ]
        mock_page = self._create_mock_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect()

        assert len(results) == 1
        obj = results[0]
        assert isinstance(obj, OSSAssetObject)
        assert obj.uri == "oss://test-bucket/data/warehouse/file1.parquet"
        assert obj.size == 12345
        assert obj.modified_at == modified_time
        assert obj.filesystem == AssetFilesystem.OSS

    def test_inspect_null_modified_at(self):
        """Test inspect handles objects with null modified_at."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        # Mock object with None as last_modified
        mock_obj = Mock()
        mock_obj.key = "data/warehouse/file1.parquet"
        mock_obj.size = 1024
        mock_obj.last_modified = None

        mock_page = self._create_mock_page([mock_obj])

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            # Should not raise exception
            results = asset.inspect()

        assert len(results) == 1
        assert results[0].modified_at is None

    def test_inspect_null_size(self):
        """Test inspect handles objects with null size."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        now = datetime.now(timezone.utc)
        mock_obj = Mock()
        mock_obj.key = "data/warehouse/file1.parquet"
        mock_obj.size = None
        mock_obj.last_modified = now

        mock_page = self._create_mock_page([mock_obj])

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect()

        assert len(results) == 1
        assert results[0].size is None

    def test_inspect_with_access_parameter(self):
        """Test inspect passes access parameter to _get_iterator."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        mock_access = Mock()
        now = datetime.now(timezone.utc)
        mock_objects = [
            self._create_mock_oss_object("data/warehouse/file1.parquet", 1024, now),
        ]
        mock_page = self._create_mock_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]) as mock_get_iter:
            results = asset.inspect(access=mock_access)

            # Verify access parameter was passed
            mock_get_iter.assert_called_once_with(mock_access)
            assert len(results) == 1

    def test_inspect_complex_glob_pattern(self):
        """Test inspect with complex glob patterns including wildcards."""
        asset = OSSAsset(
            glob="oss://test-bucket/year=*/month=*/day=*/*.parquet",
            region="cn-hangzhou",
        )

        now = datetime.now(timezone.utc)
        mock_objects = [
            self._create_mock_oss_object(
                "year=2024/month=01/day=15/data.parquet", 1024, now
            ),  # Matches
            self._create_mock_oss_object(
                "year=2024/month=01/summary.csv", 2048, now
            ),  # Wrong extension
            self._create_mock_oss_object(
                "year=2024/month=02/day=20/records.parquet", 3072, now
            ),  # Matches
            self._create_mock_oss_object("data/file.parquet", 4096, now),  # Wrong path
        ]
        mock_page = self._create_mock_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect()

        assert len(results) == 2
        uris = [obj.uri for obj in results]
        assert "oss://test-bucket/year=2024/month=01/day=15/data.parquet" in uris
        assert "oss://test-bucket/year=2024/month=02/day=20/records.parquet" in uris

    def test_inspect_combined_filters(self):
        """Test inspect with all filters combined: since, until, limit."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        since_time = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        until_time = datetime(2024, 1, 10, 0, 0, 0, tzinfo=timezone.utc)

        mock_objects = [
            self._create_mock_oss_object(
                "data/archive/file1.parquet",
                1024,
                datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            ),  # Too old
            self._create_mock_oss_object(
                "data/recent/file2.parquet",
                2048,
                datetime(2024, 1, 3, 0, 0, 0, tzinfo=timezone.utc),
            ),  # In range
            self._create_mock_oss_object(
                "data/recent/file3.parquet",
                3072,
                datetime(2024, 1, 5, 0, 0, 0, tzinfo=timezone.utc),
            ),  # In range
            self._create_mock_oss_object(
                "data/recent/file4.parquet",
                4096,
                datetime(2024, 1, 7, 0, 0, 0, tzinfo=timezone.utc),
            ),  # In range
            self._create_mock_oss_object(
                "data/recent/file5.parquet",
                5120,
                datetime(2024, 1, 9, 0, 0, 0, tzinfo=timezone.utc),
            ),  # In range
            self._create_mock_oss_object(
                "data/latest/file6.parquet",
                6144,
                datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
            ),  # Too new
        ]
        mock_page = self._create_mock_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect(since=since_time, until=until_time, limit=2)

        # Should return only 2 results (due to limit) that are within time range
        assert len(results) == 2
        assert all(
            since_time <= obj.modified_at <= until_time for obj in results if obj.modified_at
        )

    def test_inspect_sorting_with_none_modified_at(self):
        """Test inspect sorting handles objects with None modified_at correctly."""
        asset = OSSAsset(
            glob="oss://test-bucket/data/**/*.parquet",
            region="cn-hangzhou",
        )

        time1 = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        time2 = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)

        # Mix of objects with and without modified_at
        mock_obj_none1 = Mock()
        mock_obj_none1.key = "data/warehouse/file_none1.parquet"
        mock_obj_none1.size = 1024
        mock_obj_none1.last_modified = None

        mock_obj_none2 = Mock()
        mock_obj_none2.key = "data/warehouse/file_none2.parquet"
        mock_obj_none2.size = 2048
        mock_obj_none2.last_modified = None

        mock_objects = [
            self._create_mock_oss_object("data/warehouse/file1.parquet", 3072, time1),
            mock_obj_none1,
            self._create_mock_oss_object("data/warehouse/file2.parquet", 4096, time2),
            mock_obj_none2,
        ]
        mock_page = self._create_mock_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            # Should not raise exception during sorting
            results = asset.inspect()

        assert len(results) == 4
        # Objects with None modified_at should be sorted to the end (treated as datetime.min with UTC)
        assert results[0].modified_at == time2  # Newest first
        assert results[1].modified_at == time1  # Older
        assert results[2].modified_at is None  # None values at end
        assert results[3].modified_at is None
