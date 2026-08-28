"""Unit tests for LocalAsset."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from fsspec.implementations.local import LocalFileSystem

from assetlake.control.access.local.local import LocalAccess
from assetlake.control.asset.local.asset import LocalAsset, LocalAssetDomain
from assetlake.control.asset.local.object import LocalAssetObject
from assetlake.domain.asset.filesystem import AssetFilesystem
from assetlake.domain.asset.objectkind import AssetObjectkind


class TestLocalAssetDomain:
    """Test LocalAssetDomain model."""

    def test_filesystem_defaults_to_local(self):
        """Test that filesystem is always LOCAL."""
        domain = LocalAssetDomain(glob="/data/**/*.parquet")
        assert domain.filesystem == AssetFilesystem.LOCAL

    def test_create_with_all_fields(self):
        """Test creating domain with all fields."""
        domain = LocalAssetDomain(
            glob="/data/**/*.csv",
            name="test_asset",
            objectkind=AssetObjectkind.CSV,
            partitions=["year", "month"],
            description="Test asset",
            owner="data_team",
            metadata={"source": "test"},
            tags={"env": "dev"},
        )

        assert domain.glob == "/data/**/*.csv"
        assert domain.name == "test_asset"
        assert domain.objectkind == AssetObjectkind.CSV
        assert domain.partitions == ["year", "month"]
        assert domain.description == "Test asset"
        assert domain.owner == "data_team"
        assert domain.metadata == {"source": "test"}
        assert domain.tags == {"env": "dev"}


class TestLocalAssetCreation:
    """Test LocalAsset instantiation."""

    def test_create_minimal_asset(self):
        """Test creating asset with minimal required fields."""
        asset = LocalAsset(glob="/data/**/*.parquet")

        assert asset.glob == "/data/**/*.parquet"
        assert asset.filesystem == AssetFilesystem.LOCAL
        assert asset.name is None
        assert asset.partitions == []

    def test_create_full_asset(self):
        """Test creating asset with all fields."""
        asset = LocalAsset(
            glob="/warehouse/year=*/month=*/*.parquet",
            name="sales_data",
            objectkind=AssetObjectkind.PARQUET,
            partitions=["year", "month"],
            description="Sales transaction data",
            owner="analytics_team",
            metadata={"format": "parquet", "compression": "snappy"},
            tags={"category": "sales", "env": "prod"},
        )

        assert asset.glob == "/warehouse/year=*/month=*/*.parquet"
        assert asset.name == "sales_data"
        assert asset.objectkind == AssetObjectkind.PARQUET
        assert asset.partitions == ["year", "month"]
        assert asset.description == "Sales transaction data"
        assert asset.owner == "analytics_team"
        assert asset.metadata == {"format": "parquet", "compression": "snappy"}
        assert asset.tags == {"category": "sales", "env": "prod"}

    def test_domain_class_is_set(self):
        """Test that _domain_class is properly set."""
        assert LocalAsset._domain_class is LocalAssetDomain

    def test_domain_attribute_accessible(self):
        """Test that domain attribute is accessible through __getattr__."""
        asset = LocalAsset(glob="/data/*.csv", name="test")
        assert hasattr(asset, "domain")
        assert isinstance(asset.domain, LocalAssetDomain)


class TestLocalAssetGetMount:
    """Test LocalAsset.get_mount method."""

    def test_get_mount_without_access(self):
        """Test get_mount returns LocalFileSystem without access."""
        asset = LocalAsset(glob="/data/**/*.parquet")
        mount = asset.get_mount()

        assert isinstance(mount, LocalFileSystem)
        assert mount.auto_mkdir is True

    def test_get_mount_with_access(self):
        """Test get_mount with LocalAccess."""
        asset = LocalAsset(glob="/data/**/*.parquet")
        access = LocalAccess()
        mount = asset.get_mount(access)

        assert isinstance(mount, LocalFileSystem)
        assert mount.auto_mkdir is True


class TestLocalAssetInspectBasics:
    """Test basic inspect functionality."""

    def test_inspect_non_existent_path(self, tmp_path: Path):
        """Test inspect on non-existent directory returns empty list."""
        non_existent = tmp_path / "does_not_exist"
        asset = LocalAsset(glob=f"{non_existent}/**/*.parquet")

        results = asset.inspect()
        assert results == []

    def test_inspect_empty_directory(self, tmp_path: Path):
        """Test inspect on empty directory returns empty list."""
        asset = LocalAsset(glob=f"{tmp_path}/**/*.parquet")

        results = asset.inspect()
        assert results == []

    def test_inspect_returns_localassetobject_list(self, tmp_path: Path):
        """Test that inspect returns list of LocalAssetObject."""
        (tmp_path / "file.parquet").write_text("test data")
        asset = LocalAsset(glob=f"{tmp_path}/**/*.parquet")

        results = asset.inspect()
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], LocalAssetObject)


class TestLocalAssetInspectGlobMatching:
    """Test glob pattern matching in inspect."""

    def test_inspect_simple_glob_pattern(self, tmp_path: Path):
        """Test inspect with simple wildcard pattern."""
        (tmp_path / "file1.parquet").write_text("data1")
        (tmp_path / "file2.parquet").write_text("data2")
        (tmp_path / "file3.csv").write_text("data3")

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results = asset.inspect()

        assert len(results) == 2
        names = {Path(obj.uri).name for obj in results}
        assert names == {"file1.parquet", "file2.parquet"}

    def test_inspect_recursive_glob_pattern(self, tmp_path: Path):
        """Test inspect with recursive ** pattern."""
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "file1.csv").write_text("data1")
        (tmp_path / "data" / "nested").mkdir()
        (tmp_path / "data" / "nested" / "file2.csv").write_text("data2")

        asset = LocalAsset(glob=f"{tmp_path}/**/*.csv")
        results = asset.inspect()

        assert len(results) == 2

    def test_inspect_specific_file_extension(self, tmp_path: Path):
        """Test inspect filters by file extension."""
        (tmp_path / "data.parquet").write_text("parquet")
        (tmp_path / "data.csv").write_text("csv")
        (tmp_path / "data.json").write_text("json")

        asset = LocalAsset(glob=f"{tmp_path}/*.csv")
        results = asset.inspect()

        assert len(results) == 1
        assert results[0].uri.endswith(".csv")

    def test_inspect_with_partitioned_glob(self, tmp_path: Path):
        """Test inspect with partitioned directory structure."""
        for year in ["2023", "2024"]:
            for month in ["01", "02"]:
                dir_path = tmp_path / f"year={year}" / f"month={month}"
                dir_path.mkdir(parents=True)
                (dir_path / "data.parquet").write_text(f"data-{year}-{month}")

        asset = LocalAsset(glob=f"{tmp_path}/year=*/month=*/*.parquet")
        results = asset.inspect()

        assert len(results) == 4  # 2 years × 2 months


class TestLocalAssetInspectMetadata:
    """Test that inspect extracts correct metadata."""

    def test_inspect_extracts_uri(self, tmp_path: Path):
        """Test that inspect extracts correct URI."""
        file_path = tmp_path / "test.parquet"
        file_path.write_text("data")

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results = asset.inspect()

        assert len(results) == 1
        assert results[0].uri == str(file_path)

    def test_inspect_extracts_size(self, tmp_path: Path):
        """Test that inspect extracts file size."""
        file_path = tmp_path / "test.parquet"
        file_path.write_bytes(b"x" * 1024)

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results = asset.inspect()

        assert len(results) == 1
        assert results[0].size == 1024

    def test_inspect_extracts_modified_at(self, tmp_path: Path):
        """Test that inspect extracts modification time."""
        file_path = tmp_path / "test.csv"
        file_path.write_text("data")

        asset = LocalAsset(glob=f"{tmp_path}/*.csv")
        results = asset.inspect()

        assert len(results) == 1
        assert results[0].modified_at is not None
        assert isinstance(results[0].modified_at, datetime)

    def test_inspect_extracts_type(self, tmp_path: Path):
        """Test that inspect extracts file type."""
        file_path = tmp_path / "test.parquet"
        file_path.write_text("data")

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results = asset.inspect()

        assert len(results) == 1
        assert results[0].type == "file"

    def test_inspect_extracts_metadata_fields(self, tmp_path: Path):
        """Test that inspect extracts additional metadata."""
        file_path = tmp_path / "test.parquet"
        file_path.write_text("data")

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results = asset.inspect()

        assert len(results) == 1
        metadata = results[0].metadata
        assert isinstance(metadata, dict)
        # Check that common metadata fields are present
        assert "mode" in metadata or "uid" in metadata or "gid" in metadata


class TestLocalAssetInspectTimeFiltering:
    """Test time-based filtering in inspect."""

    def test_inspect_with_since_filter(self, tmp_path: Path):
        """Test inspect filters files modified after since time."""
        file1 = tmp_path / "old.parquet"
        file2 = tmp_path / "new.parquet"

        file1.write_text("old data")
        time.sleep(0.1)
        since_time = datetime.now(timezone.utc)
        time.sleep(0.1)
        file2.write_text("new data")

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results = asset.inspect(since=since_time)

        # Should only include file2
        assert len(results) == 1
        assert results[0].uri == str(file2)

    def test_inspect_with_until_filter(self, tmp_path: Path):
        """Test inspect filters files modified before until time."""
        file1 = tmp_path / "old.parquet"
        file2 = tmp_path / "new.parquet"

        file1.write_text("old data")
        time.sleep(0.1)
        until_time = datetime.now(timezone.utc)
        time.sleep(0.1)
        file2.write_text("new data")

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results = asset.inspect(until=until_time)

        # Should only include file1
        assert len(results) == 1
        assert results[0].uri == str(file1)

    def test_inspect_with_since_and_until(self, tmp_path: Path):
        """Test inspect with both since and until filters."""
        file1 = tmp_path / "before.parquet"
        file2 = tmp_path / "during.parquet"
        file3 = tmp_path / "after.parquet"

        file1.write_text("before")
        time.sleep(0.1)
        since_time = datetime.now(timezone.utc)
        time.sleep(0.1)
        file2.write_text("during")
        time.sleep(0.1)
        until_time = datetime.now(timezone.utc)
        time.sleep(0.1)
        file3.write_text("after")

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results = asset.inspect(since=since_time, until=until_time)

        # Should only include file2
        assert len(results) == 1
        assert results[0].uri == str(file2)

    def test_inspect_with_none_time_filters(self, tmp_path: Path):
        """Test inspect with None time filters returns all files."""
        (tmp_path / "file1.parquet").write_text("data1")
        (tmp_path / "file2.parquet").write_text("data2")

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results = asset.inspect(since=None, until=None)

        assert len(results) == 2


class TestLocalAssetInspectLimit:
    """Test limit parameter in inspect."""

    def test_inspect_with_limit(self, tmp_path: Path):
        """Test inspect respects limit parameter."""
        for i in range(10):
            (tmp_path / f"file{i}.parquet").write_text(f"data{i}")

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results = asset.inspect(limit=3)

        assert len(results) == 3

    def test_inspect_limit_returns_most_recent(self, tmp_path: Path):
        """Test that limit returns most recently modified files."""
        # Create files with different modification times
        for i in range(5):
            file = tmp_path / f"file{i}.parquet"
            file.write_text(f"data{i}")
            if i < 4:
                time.sleep(0.05)

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results = asset.inspect(limit=2)

        assert len(results) == 2
        # Results should be sorted by modified_at descending
        assert results[0].modified_at >= results[1].modified_at

    def test_inspect_limit_none_returns_all(self, tmp_path: Path):
        """Test inspect with limit=None returns all files."""
        for i in range(5):
            (tmp_path / f"file{i}.csv").write_text(f"data{i}")

        asset = LocalAsset(glob=f"{tmp_path}/*.csv")
        results = asset.inspect(limit=None)

        assert len(results) == 5

    def test_inspect_limit_greater_than_available(self, tmp_path: Path):
        """Test inspect when limit exceeds available files."""
        (tmp_path / "file1.parquet").write_text("data1")
        (tmp_path / "file2.parquet").write_text("data2")

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results = asset.inspect(limit=10)

        assert len(results) == 2


class TestLocalAssetInspectSorting:
    """Test that inspect returns results sorted by modification time."""

    def test_inspect_sorts_by_modified_at_descending(self, tmp_path: Path):
        """Test that results are sorted by modified_at in descending order."""
        files = []
        for i in range(3):
            file = tmp_path / f"file{i}.parquet"
            file.write_text(f"data{i}")
            files.append(file)
            time.sleep(0.05)

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results = asset.inspect()

        assert len(results) == 3
        # Most recent file should be first
        for i in range(len(results) - 1):
            assert results[i].modified_at >= results[i + 1].modified_at


class TestLocalAssetInspectPartitions:
    """Test partition extraction in inspect."""

    def test_inspect_extracts_partitions(self, tmp_path: Path):
        """Test that partitions are extracted from file paths."""
        dir_path = tmp_path / "year=2024" / "month=03"
        dir_path.mkdir(parents=True)
        (dir_path / "data.parquet").write_text("data")

        asset = LocalAsset(glob=f"{tmp_path}/year=*/month=*/*.parquet")
        results = asset.inspect()

        assert len(results) == 1
        assert results[0].partitions == {"year": "2024", "month": "03"}

    def test_inspect_multiple_files_different_partitions(self, tmp_path: Path):
        """Test inspect with multiple files in different partitions."""
        for year in ["2023", "2024"]:
            dir_path = tmp_path / f"year={year}"
            dir_path.mkdir(parents=True)
            (dir_path / "data.csv").write_text(f"data-{year}")

        asset = LocalAsset(glob=f"{tmp_path}/year=*/*.csv")
        results = asset.inspect()

        assert len(results) == 2
        partitions = [obj.partitions for obj in results]
        assert {"year": "2023"} in partitions
        assert {"year": "2024"} in partitions


class TestLocalAssetInspectWithAccess:
    """Test inspect with access parameter."""

    def test_inspect_with_none_access(self, tmp_path: Path):
        """Test inspect with access=None works correctly."""
        (tmp_path / "file.parquet").write_text("data")

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results = asset.inspect(access=None)

        assert len(results) == 1

    def test_inspect_with_local_access(self, tmp_path: Path):
        """Test inspect with LocalAccess instance."""
        (tmp_path / "file.csv").write_text("data")

        asset = LocalAsset(glob=f"{tmp_path}/*.csv")
        access = LocalAccess()
        results = asset.inspect(access=access)

        assert len(results) == 1


class TestLocalAssetSerialization:
    """Test from_dict, from_domain, export, and describe methods."""

    def test_from_dict(self):
        """Test creating asset from dictionary."""
        data = {
            "glob": "/data/**/*.parquet",
            "name": "test_asset",
            "filesystem": AssetFilesystem.LOCAL,
            "tags": {"env": "test"},
        }

        asset = LocalAsset.from_dict(data)
        assert isinstance(asset, LocalAsset)
        assert asset.glob == "/data/**/*.parquet"
        assert asset.name == "test_asset"
        assert asset.tags == {"env": "test"}

    def test_from_domain(self):
        """Test creating asset from domain model."""
        domain = LocalAssetDomain(
            glob="/data/**/*.csv",
            name="test_asset",
            tags={"category": "sales"},
        )

        asset = LocalAsset.from_domain(domain)
        assert isinstance(asset, LocalAsset)
        assert asset.glob == "/data/**/*.csv"
        assert asset.name == "test_asset"
        assert asset.tags == {"category": "sales"}

    def test_export(self):
        """Test exporting asset to dictionary."""
        asset = LocalAsset(
            glob="/warehouse/**/*.parquet",
            name="warehouse_data",
            tags={"env": "prod"},
        )

        exported = asset.export()
        assert isinstance(exported, dict)
        assert exported["glob"] == "/warehouse/**/*.parquet"
        assert exported["name"] == "warehouse_data"
        assert exported["tags"] == {"env": "prod"}

    def test_describe(self):
        """Test describe returns JSON string."""
        asset = LocalAsset(
            glob="/data/**/*.csv",
            name="test_asset",
        )

        description = asset.describe()
        assert isinstance(description, str)
        assert "/data/**/*.csv" in description
        assert "test_asset" in description

    def test_roundtrip_dict_serialization(self):
        """Test asset can be serialized and deserialized."""
        original = LocalAsset(
            glob="/data/**/*.parquet",
            name="test_asset",
            partitions=["year", "month"],
            description="Test description",
            owner="test_owner",
            metadata={"key": "value"},
            tags={"env": "dev"},
        )

        exported = original.export()
        restored = LocalAsset.from_dict(exported)

        assert restored.glob == original.glob
        assert restored.name == original.name
        assert restored.partitions == original.partitions
        assert restored.description == original.description
        assert restored.owner == original.owner
        assert restored.metadata == original.metadata
        assert restored.tags == original.tags


class TestLocalAssetEdgeCases:
    """Test edge cases and error handling."""

    def test_glob_with_no_matches(self, tmp_path: Path):
        """Test glob that doesn't match any files."""
        (tmp_path / "file.csv").write_text("data")

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results = asset.inspect()

        assert results == []

    def test_inspect_with_symlinks(self, tmp_path: Path):
        """Test inspect handles symlinks."""
        real_file = tmp_path / "real.parquet"
        real_file.write_text("data")

        link = tmp_path / "link.parquet"
        link.symlink_to(real_file)

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results = asset.inspect()

        # Should find both real file and symlink
        assert len(results) >= 1

    def test_inspect_handles_special_characters_in_path(self, tmp_path: Path):
        """Test inspect with special characters in file names."""
        special_dir = tmp_path / "data (test)"
        special_dir.mkdir()
        (special_dir / "file-name_123.parquet").write_text("data")

        asset = LocalAsset(glob=f"{special_dir}/*.parquet")
        results = asset.inspect()

        assert len(results) == 1

    def test_multiple_inspects_are_independent(self, tmp_path: Path):
        """Test that multiple inspect calls are independent."""
        (tmp_path / "file.parquet").write_text("data")

        asset = LocalAsset(glob=f"{tmp_path}/*.parquet")
        results1 = asset.inspect()
        results2 = asset.inspect()

        assert results1 == results2
        # Ensure they're different list instances
        assert results1 is not results2


class TestLocalAssetQuality:
    """Test LocalAsset.quality method."""

    def test_quality_raises_error_for_non_parquet(self, tmp_path: Path):
        """Test quality raises ValueError for non-PARQUET objectkind."""
        asset = LocalAsset(
            glob=f"{tmp_path}/*.csv",
            objectkind=AssetObjectkind.CSV,
        )

        try:
            asset.quality()
            assert False, "Expected ValueError to be raised"
        except ValueError as e:
            assert "Quality check is only supported for PARQUET" in str(e)

    def test_quality_with_glob_pattern(self, tmp_path: Path):
        """Test quality using glob pattern to query parquet metadata."""
        import duckdb

        # Create test parquet file using duckdb
        test_file = tmp_path / "test_data.parquet"
        conn = duckdb.connect(":memory:")
        conn.execute(
            f"COPY (SELECT 1 as id, 'Alice' as name, 25 as age) TO '{test_file}' (FORMAT PARQUET)"
        )
        conn.close()

        # Create asset and check quality
        asset = LocalAsset(
            glob=f"{tmp_path}/*.parquet",
            objectkind=AssetObjectkind.PARQUET,
        )
        results = asset.quality()

        # Verify results structure
        assert isinstance(results, list)
        assert len(results) > 0
        assert isinstance(results[0], dict)
        # Check for common parquet metadata fields
        assert "file_name" in results[0]

    def test_quality_with_objects_list(self, tmp_path: Path):
        """Test quality using explicit list of objects."""
        import duckdb

        # Create test parquet files
        test_file1 = tmp_path / "data1.parquet"
        test_file2 = tmp_path / "data2.parquet"
        conn = duckdb.connect(":memory:")
        conn.execute(f"COPY (SELECT 1 as id, 'Bob' as name) TO '{test_file1}' (FORMAT PARQUET)")
        conn.execute(f"COPY (SELECT 2 as id, 'Charlie' as name) TO '{test_file2}' (FORMAT PARQUET)")
        conn.close()

        # Create asset
        asset = LocalAsset(
            glob=f"{tmp_path}/*.parquet",
            objectkind=AssetObjectkind.PARQUET,
        )

        # Create object list
        objects = [
            LocalAssetObject(uri=str(test_file1)),
            LocalAssetObject(uri=str(test_file2)),
        ]

        # Check quality with objects
        results = asset.quality(objects=objects)

        assert isinstance(results, list)
        assert len(results) > 0

    def test_quality_with_custom_connection(self, tmp_path: Path):
        """Test quality using custom duckdb connection."""
        import duckdb

        # Create test parquet file
        test_file = tmp_path / "custom.parquet"
        conn = duckdb.connect(":memory:")
        conn.execute(
            f"COPY (SELECT 1 as id, 'David' as name, 30 as age) TO '{test_file}' (FORMAT PARQUET)"
        )

        # Create asset and check quality with custom connection
        asset = LocalAsset(
            glob=f"{tmp_path}/*.parquet",
            objectkind=AssetObjectkind.PARQUET,
        )
        results = asset.quality(conn=conn)

        assert isinstance(results, list)
        assert len(results) > 0
        conn.close()

    def test_quality_with_access_parameter(self, tmp_path: Path):
        """Test quality with LocalAccess parameter."""
        import duckdb

        # Create test parquet file
        test_file = tmp_path / "access_test.parquet"
        conn = duckdb.connect(":memory:")
        conn.execute(f"COPY (SELECT 1 as id, 'Eve' as name) TO '{test_file}' (FORMAT PARQUET)")
        conn.close()

        # Create asset and check quality with access
        asset = LocalAsset(
            glob=f"{tmp_path}/*.parquet",
            objectkind=AssetObjectkind.PARQUET,
        )
        access = LocalAccess()
        results = asset.quality(access=access)

        assert isinstance(results, list)
        assert len(results) > 0

    def test_quality_returns_metadata_structure(self, tmp_path: Path):
        """Test that quality returns proper parquet metadata structure."""
        import duckdb

        # Create test parquet file with known data
        test_file = tmp_path / "metadata_test.parquet"
        conn = duckdb.connect(":memory:")
        conn.execute(
            f"COPY (SELECT i as id, 'user_' || i as name FROM range(100) t(i)) "
            f"TO '{test_file}' (FORMAT PARQUET)"
        )
        conn.close()

        # Check quality
        asset = LocalAsset(
            glob=f"{tmp_path}/*.parquet",
            objectkind=AssetObjectkind.PARQUET,
        )
        results = asset.quality()

        assert isinstance(results, list)
        assert len(results) > 0
        # Verify metadata contains file_name
        result = results[0]
        assert "file_name" in result

    def test_quality_with_no_matching_files(self, tmp_path: Path):
        """Test quality with glob that matches no files."""
        import duckdb

        asset = LocalAsset(
            glob=f"{tmp_path}/nonexistent/*.parquet",
            objectkind=AssetObjectkind.PARQUET,
        )

        # DuckDB raises IOException when no files match the pattern
        try:
            _ = asset.quality()
            assert False, "Expected IOException to be raised"
        except duckdb.IOException as e:
            assert "No files found" in str(e)

    def test_quality_with_empty_objects_list(self, tmp_path: Path):
        """Test quality behavior with empty objects list."""
        import duckdb

        # Create a test file for glob fallback
        test_file = tmp_path / "fallback.parquet"
        conn = duckdb.connect(":memory:")
        conn.execute(f"COPY (SELECT 1 as id) TO '{test_file}' (FORMAT PARQUET)")
        conn.close()

        asset = LocalAsset(
            glob=f"{tmp_path}/*.parquet",
            objectkind=AssetObjectkind.PARQUET,
        )

        # Pass None explicitly to use glob pattern
        results = asset.quality(objects=None)
        assert isinstance(results, list)
