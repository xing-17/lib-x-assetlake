"""Unit tests for S3Asset."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from assetlake.control.asset.s3.asset import S3Asset, S3AssetDomain
from assetlake.control.asset.s3.object import S3AssetObject
from assetlake.domain.asset.filesystem import AssetFilesystem
from assetlake.domain.asset.objectkind import AssetObjectkind


class TestS3AssetDomain:
    """Test S3AssetDomain model."""

    def test_filesystem_defaults_to_s3(self):
        domain = S3AssetDomain(glob="s3://my-bucket/data/**/*.parquet")
        assert domain.filesystem == AssetFilesystem.S3

    def test_create_with_all_fields(self):
        domain = S3AssetDomain(
            glob="s3://test-bucket/warehouse/**/*.csv",
            region="us-east-1",
            name="test_asset",
            objectkind=AssetObjectkind.CSV,
            partitions=["year", "month"],
            description="Test asset",
            owner="data_team",
            metadata={"source": "test"},
            tags={"env": "dev"},
        )
        assert domain.glob == "s3://test-bucket/warehouse/**/*.csv"
        assert domain.region == "us-east-1"
        assert domain.name == "test_asset"
        assert domain.objectkind == AssetObjectkind.CSV
        assert domain.partitions == ["year", "month"]

    def test_region_is_optional(self):
        domain = S3AssetDomain(glob="s3://my-bucket/data/**/*.parquet")
        assert domain.region is None

    def test_bucket_extraction(self):
        domain = S3AssetDomain(glob="s3://my-bucket/data/**/*.parquet")
        assert domain.bucket == "my-bucket"

    def test_common_prefix_extraction(self):
        domain = S3AssetDomain(glob="s3://my-bucket/data/warehouse/**/*.parquet")
        assert domain.common_prefix == "data/warehouse/"

    def test_object_pattern_extraction(self):
        domain = S3AssetDomain(glob="s3://my-bucket/data/**/*.parquet")
        assert domain.object_pattern == "**/*.parquet"


class TestS3AssetCreation:
    """Test S3Asset instantiation."""

    def test_create_minimal_asset(self):
        asset = S3Asset(glob="s3://my-bucket/data/**/*.parquet")
        assert asset.domain.filesystem == AssetFilesystem.S3

    def test_create_with_region(self):
        asset = S3Asset(
            glob="s3://my-bucket/data/**/*.parquet",
            region="us-west-2",
        )
        assert asset.region == "us-west-2"

    def test_domain_attribute_accessible(self):
        asset = S3Asset(
            glob="s3://my-bucket/data/*.csv",
            region="us-east-1",
            name="test",
        )
        assert hasattr(asset, "domain")
        assert isinstance(asset.domain, S3AssetDomain)

    def test_bucket_property_through_domain(self):
        asset = S3Asset(glob="s3://test-bucket/data/**/*.parquet")
        assert asset.domain.bucket == "test-bucket"


class TestS3AssetObjectKinds:
    """Test S3Asset with different object kinds."""

    def test_parquet_objectkind(self):
        asset = S3Asset(
            glob="s3://bucket/data/**/*.parquet",
            objectkind=AssetObjectkind.PARQUET,
        )
        assert asset.objectkind == AssetObjectkind.PARQUET

    def test_csv_objectkind(self):
        asset = S3Asset(
            glob="s3://bucket/data/**/*.csv",
            objectkind=AssetObjectkind.CSV,
        )
        assert asset.objectkind == AssetObjectkind.CSV

    def test_no_partitions_default(self):
        asset = S3Asset(glob="s3://bucket/data/*.parquet")
        assert asset.partitions == []

    def test_multiple_partitions(self):
        asset = S3Asset(
            glob="s3://bucket/year=*/month=*/day=*/*.parquet",
            partitions=["year", "month", "day"],
        )
        assert asset.partitions == ["year", "month", "day"]


class TestS3AssetInspect:
    """Tests for S3Asset.inspect() method."""

    def _make_s3_obj(self, key: str, size: int, last_modified: datetime) -> dict:
        return {"Key": key, "Size": size, "LastModified": last_modified}

    def _make_page(self, objects: list) -> dict:
        return {"Contents": objects}

    def test_inspect_basic_no_filters(self):
        asset = S3Asset(glob="s3://test-bucket/data/**/*.parquet")

        now = datetime.now(timezone.utc)
        mock_objects = [
            self._make_s3_obj("data/warehouse/file1.parquet", 1024, now),
            self._make_s3_obj("data/raw/file2.parquet", 2048, now),
            self._make_s3_obj("data/archive/subdir/file3.parquet", 3072, now),
        ]
        mock_page = self._make_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect()

        assert len(results) == 3
        assert all(isinstance(obj, S3AssetObject) for obj in results)
        uris = {obj.uri for obj in results}
        assert "s3://test-bucket/data/warehouse/file1.parquet" in uris
        assert "s3://test-bucket/data/raw/file2.parquet" in uris

    def test_inspect_empty_page(self):
        asset = S3Asset(glob="s3://test-bucket/data/**/*.parquet")

        with patch.object(asset, "_get_iterator", return_value=[{}]):
            results = asset.inspect()

        assert results == []

    def test_inspect_since_filter(self):
        asset = S3Asset(glob="s3://test-bucket/data/**/*.parquet")

        since_time = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        mock_objects = [
            self._make_s3_obj(
                "data/archive/old.parquet", 1024, datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            ),
            self._make_s3_obj(
                "data/recent/new1.parquet",
                2048,
                datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            ),
            self._make_s3_obj(
                "data/latest/new2.parquet", 3072, datetime(2024, 1, 3, 0, 0, 0, tzinfo=timezone.utc)
            ),
        ]
        mock_page = self._make_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect(since=since_time)

        assert len(results) == 2
        assert all(obj.modified_at >= since_time for obj in results if obj.modified_at)

    def test_inspect_until_filter(self):
        asset = S3Asset(glob="s3://test-bucket/data/**/*.parquet")

        until_time = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        mock_objects = [
            self._make_s3_obj(
                "data/archive/old1.parquet",
                1024,
                datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            ),
            self._make_s3_obj(
                "data/archive/old2.parquet",
                2048,
                datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            self._make_s3_obj(
                "data/recent/new.parquet", 3072, datetime(2024, 1, 3, 0, 0, 0, tzinfo=timezone.utc)
            ),
        ]
        mock_page = self._make_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect(until=until_time)

        assert len(results) == 2
        assert all(obj.modified_at <= until_time for obj in results if obj.modified_at)

    def test_inspect_since_and_until_filter(self):
        asset = S3Asset(glob="s3://test-bucket/data/**/*.parquet")

        since_time = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        until_time = datetime(2024, 1, 4, 0, 0, 0, tzinfo=timezone.utc)
        mock_objects = [
            self._make_s3_obj(
                "data/archive/too_old.parquet",
                1024,
                datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            ),
            self._make_s3_obj(
                "data/recent/in_range1.parquet",
                2048,
                datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            ),
            self._make_s3_obj(
                "data/recent/in_range2.parquet",
                3072,
                datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
            ),
            self._make_s3_obj(
                "data/latest/too_new.parquet",
                4096,
                datetime(2024, 1, 5, 0, 0, 0, tzinfo=timezone.utc),
            ),
        ]
        mock_page = self._make_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect(since=since_time, until=until_time)

        assert len(results) == 2
        assert all(
            since_time <= obj.modified_at <= until_time for obj in results if obj.modified_at
        )

    def test_inspect_limit(self):
        asset = S3Asset(glob="s3://test-bucket/data/**/*.parquet")

        now = datetime.now(timezone.utc)
        mock_objects = [
            self._make_s3_obj(f"data/warehouse/file{i}.parquet", 1024 * i, now)
            for i in range(1, 11)
        ]
        mock_page = self._make_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect(limit=3)

        assert len(results) == 3

    def test_inspect_glob_pattern_matching(self):
        asset = S3Asset(glob="s3://test-bucket/data/**/*.parquet")

        now = datetime.now(timezone.utc)
        mock_objects = [
            self._make_s3_obj("data/warehouse/file1.parquet", 1024, now),
            self._make_s3_obj("data/warehouse/file2.csv", 2048, now),
            self._make_s3_obj("data/archive/subdir/file3.parquet", 3072, now),
            self._make_s3_obj("other/warehouse/file4.parquet", 4096, now),
        ]
        mock_page = self._make_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect()

        assert len(results) == 2
        uris = {obj.uri for obj in results}
        assert "s3://test-bucket/data/warehouse/file1.parquet" in uris
        assert "s3://test-bucket/data/archive/subdir/file3.parquet" in uris

    def test_inspect_sorted_by_modified_at_desc(self):
        asset = S3Asset(glob="s3://test-bucket/data/**/*.parquet")

        time1 = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        time2 = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        time3 = datetime(2024, 1, 3, 0, 0, 0, tzinfo=timezone.utc)
        mock_objects = [
            self._make_s3_obj("data/warehouse/file2.parquet", 2048, time2),
            self._make_s3_obj("data/warehouse/file1.parquet", 1024, time1),
            self._make_s3_obj("data/warehouse/file3.parquet", 3072, time3),
        ]
        mock_page = self._make_page(mock_objects)

        with patch.object(asset, "_get_iterator", return_value=[mock_page]):
            results = asset.inspect()

        assert results[0].modified_at == time3
        assert results[1].modified_at == time2
        assert results[2].modified_at == time1

    def test_inspect_multiple_pages(self):
        asset = S3Asset(glob="s3://test-bucket/data/**/*.parquet")

        now = datetime.now(timezone.utc)
        page1 = self._make_page(
            [
                self._make_s3_obj("data/warehouse/file1.parquet", 1024, now),
                self._make_s3_obj("data/warehouse/file2.parquet", 2048, now),
            ]
        )
        page2 = self._make_page(
            [
                self._make_s3_obj("data/archive/file3.parquet", 3072, now),
                self._make_s3_obj("data/archive/file4.parquet", 4096, now),
            ]
        )

        with patch.object(asset, "_get_iterator", return_value=[page1, page2]):
            results = asset.inspect()

        assert len(results) == 4

    def test_inspect_limit_stops_across_pages(self):
        asset = S3Asset(glob="s3://test-bucket/data/**/*.parquet")

        now = datetime.now(timezone.utc)
        page1 = self._make_page(
            [
                self._make_s3_obj("data/warehouse/file1.parquet", 1024, now),
                self._make_s3_obj("data/warehouse/file2.parquet", 2048, now),
            ]
        )
        page2 = self._make_page(
            [
                self._make_s3_obj("data/archive/file3.parquet", 3072, now),
            ]
        )

        with patch.object(asset, "_get_iterator", return_value=[page1, page2]):
            results = asset.inspect(limit=2)

        assert len(results) == 2


class TestS3AssetGetClient:
    """Test _get_client raises ImportError when boto3 is missing."""

    def test_get_client_raises_import_error_when_boto3_missing(self):
        asset = S3Asset(glob="s3://bucket/data/**/*.parquet")

        with patch.dict("sys.modules", {"boto3": None}):
            with pytest.raises(ImportError, match="boto3"):
                asset._get_client()
