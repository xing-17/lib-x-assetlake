from __future__ import annotations

from urllib.parse import ParseResult

import pytest

from assetlake.internal.iglob import IGlob

# ---------------------------------------------------------------------------
# standardise
# ---------------------------------------------------------------------------


class TestStandardise:
    @pytest.mark.parametrize(
        "glob, expected",
        [
            # file:// prefix is stripped
            ("file:///path/to/dir", "/path/to/dir"),
            ("file:///path/to/dir/*.parquet", "/path/to/dir/*.parquet"),
            ("file:///", "/"),
            # bare local paths are left unchanged
            ("/path/to/dir", "/path/to/dir"),
            ("/path/to/dir/*.parquet", "/path/to/dir/*.parquet"),
            # cloud schemes are left unchanged
            ("s3://bucket/path", "s3://bucket/path"),
            ("oss://bucket/data/*.parquet", "oss://bucket/data/*.parquet"),
            ("gs://bucket/data/**", "gs://bucket/data/**"),
        ],
    )
    def test_standardise(self, glob: str, expected: str) -> None:
        assert IGlob.standardise(glob) == expected


# ---------------------------------------------------------------------------
# parse
# ---------------------------------------------------------------------------


class TestParse:
    def test_returns_parse_result(self) -> None:
        result = IGlob.parse("s3://bucket/path")
        assert isinstance(result, ParseResult)

    @pytest.mark.parametrize(
        "glob, scheme, netloc, path",
        [
            ("s3://bucket/data/file.parquet", "s3", "bucket", "/data/file.parquet"),
            ("/local/path/*.parquet", "", "", "/local/path/*.parquet"),
            ("file:///local/path", "file", "", "/local/path"),
            ("oss://my-bucket/key", "oss", "my-bucket", "/key"),
        ],
    )
    def test_components(self, glob: str, scheme: str, netloc: str, path: str) -> None:
        result = IGlob.parse(glob)
        assert result.scheme == scheme
        assert result.netloc == netloc
        assert result.path == path


# ---------------------------------------------------------------------------
# is_local
# ---------------------------------------------------------------------------


class TestIsLocal:
    @pytest.mark.parametrize(
        "glob",
        [
            "/path/to/dir",
            "/path/to/dir/*.parquet",
            "file:///path/to/dir",
            "file:///path/to/dir/*.parquet",
            "file:///",
        ],
    )
    def test_local_paths(self, glob: str) -> None:
        assert IGlob.is_local(glob) is True

    @pytest.mark.parametrize(
        "glob",
        [
            "s3://bucket/path",
            "s3://bucket/path/*.parquet",
            "oss://bucket/data/**",
            "gs://bucket/data/file.parquet",
            "az://container/blob",
        ],
    )
    def test_cloud_paths(self, glob: str) -> None:
        assert IGlob.is_local(glob) is False


# ---------------------------------------------------------------------------
# parse_scheme
# ---------------------------------------------------------------------------


class TestParseScheme:
    @pytest.mark.parametrize(
        "glob, expected",
        [
            ("/path/to/dir", ""),
            ("file:///path/to/dir", "file"),
            ("s3://bucket/path", "s3"),
            ("oss://bucket/path", "oss"),
            ("gs://bucket/path", "gs"),
            ("az://container/blob", "az"),
        ],
    )
    def test_parse_scheme(self, glob: str, expected: str) -> None:
        assert IGlob.parse_scheme(glob) == expected


# ---------------------------------------------------------------------------
# parse_bucket
# ---------------------------------------------------------------------------


class TestParseBucket:
    @pytest.mark.parametrize(
        "glob",
        [
            "/path/to/dir",
            "/path/to/dir/*.parquet",
            "file:///path/to/dir",
            "file:///path/to/dir/*.parquet",
        ],
    )
    def test_local_returns_none(self, glob: str) -> None:
        assert IGlob.parse_bucket(glob) is None

    @pytest.mark.parametrize(
        "glob, expected",
        [
            ("s3://my-bucket/path", "my-bucket"),
            ("s3://my-bucket", "my-bucket"),
            ("oss://oss-bucket/data/*.parquet", "oss-bucket"),
            ("gs://gcs-bucket/data/**/*.parquet", "gcs-bucket"),
            ("s3://trading-prod-datalake/bridges/source/**", "trading-prod-datalake"),
        ],
    )
    def test_cloud_returns_bucket(self, glob: str, expected: str) -> None:
        assert IGlob.parse_bucket(glob) == expected


# ---------------------------------------------------------------------------
# parse_full_prefix
# ---------------------------------------------------------------------------


class TestParseFullPrefix:
    @pytest.mark.parametrize(
        "glob, expected",
        [
            # local — leading slash preserved
            ("/data/year=2023/month=*/*.parquet", "/data/year=2023/month=*/*.parquet"),
            ("/data/file.parquet", "/data/file.parquet"),
            # file:// — path extracted as-is
            ("file:///data/dir/*.parquet", "/data/dir/*.parquet"),
            # cloud — leading slash stripped
            ("s3://bucket/data/month=*/*.parquet", "data/month=*/*.parquet"),
            ("oss://bucket/a/b/c/*.csv", "a/b/c/*.csv"),
            # cloud with no path
            ("s3://bucket", ""),
            # cloud with single-level key
            ("s3://bucket/file.parquet", "file.parquet"),
        ],
    )
    def test_parse_full_prefix(self, glob: str, expected: str) -> None:
        assert IGlob.parse_full_prefix(glob) == expected


# ---------------------------------------------------------------------------
# parse_common_prefix
# ---------------------------------------------------------------------------


class TestParseCommonPrefix:
    @pytest.mark.parametrize(
        "glob, expected",
        [
            # wildcard mid-path
            ("/data/year=2023/month=*/*.parquet", "/data/year=2023/"),
            ("s3://bucket/data/year=2023/month=*/*.parquet", "data/year=2023/"),
            # wildcard at first segment
            ("/data/*/*.parquet", "/data/"),
            ("s3://bucket/data/*/*.parquet", "data/"),
            # wildcard at root of path
            ("/*.parquet", "/"),
            ("s3://bucket/*.parquet", ""),
            ("*.parquet", ""),
            # double-star
            ("/data/**/*.parquet", "/data/"),
            ("s3://bucket/data/**/*.parquet", "data/"),
            # question-mark wildcard
            ("/data/file?.parquet", "/data/"),
            # character-class wildcard
            ("/data/file[0-9].parquet", "/data/"),
            # no wildcard — returns parent directory
            ("/data/year=2023/file.parquet", "/data/year=2023/"),
            ("s3://bucket/data/file.parquet", "data/"),
            # no wildcard, single-level key (no parent dir)
            ("s3://bucket/file.parquet", ""),
            # empty path (bucket only)
            ("s3://bucket", ""),
        ],
    )
    def test_parse_common_prefix(self, glob: str, expected: str) -> None:
        assert IGlob.parse_common_prefix(glob) == expected


# ---------------------------------------------------------------------------
# parse_object_pattern
# ---------------------------------------------------------------------------


class TestParseObjectPattern:
    @pytest.mark.parametrize(
        "glob, expected",
        [
            # wildcard at last segment
            ("/data/year=2023/month=*/*.parquet", "month=*/*.parquet"),
            ("s3://bucket/data/year=2023/month=*/*.parquet", "month=*/*.parquet"),
            # wildcard at first segment of path
            ("/data/*/*.parquet", "*/*.parquet"),
            ("s3://bucket/data/*/*.parquet", "*/*.parquet"),
            # wildcard at root
            ("/*.parquet", "*.parquet"),
            ("s3://bucket/*.parquet", "*.parquet"),
            ("*.parquet", "*.parquet"),
            # double-star
            ("/data/**/*.parquet", "**/*.parquet"),
            # question-mark wildcard
            ("/data/file?.parquet", "file?.parquet"),
            # character-class wildcard
            ("/data/file[0-9].parquet", "file[0-9].parquet"),
            # no wildcard — filename only
            ("/data/year=2023/file.parquet", "file.parquet"),
            ("s3://bucket/data/file.parquet", "file.parquet"),
            ("s3://bucket/file.parquet", "file.parquet"),
        ],
    )
    def test_parse_object_pattern(self, glob: str, expected: str) -> None:
        assert IGlob.parse_object_pattern(glob) == expected


# ---------------------------------------------------------------------------
# Integration: local vs cloud equivalence
# ---------------------------------------------------------------------------


class TestLocalCloudEquivalence:
    """
    A local path and its s3:// counterpart with the same structure
    should produce the same common_prefix / object_pattern shapes,
    differing only in the leading slash.
    """

    def test_common_prefix_shape(self) -> None:
        local = IGlob.parse_common_prefix("/data/year=2023/month=*/*.parquet")
        cloud = IGlob.parse_common_prefix("s3://bucket/data/year=2023/month=*/*.parquet")
        assert local == "/data/year=2023/"
        assert cloud == "data/year=2023/"
        assert local.lstrip("/") == cloud

    def test_object_pattern_identical(self) -> None:
        local = IGlob.parse_object_pattern("/data/year=2023/month=*/*.parquet")
        cloud = IGlob.parse_object_pattern("s3://bucket/data/year=2023/month=*/*.parquet")
        assert local == cloud == "month=*/*.parquet"

    def test_bucket_none_for_local(self) -> None:
        assert IGlob.parse_bucket("/data/**/*.parquet") is None
        assert IGlob.parse_bucket("file:///data/**/*.parquet") is None

    def test_bucket_present_for_cloud(self) -> None:
        assert IGlob.parse_bucket("s3://my-bucket/data/**/*.parquet") == "my-bucket"
