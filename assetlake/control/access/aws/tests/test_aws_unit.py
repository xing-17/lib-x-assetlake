"""Unit tests for AWS access."""

from __future__ import annotations

from assetlake.control.access.aws import AWSAccess, AWSAccessDomain
from assetlake.control.access.base.protocol import IAccessLike
from assetlake.domain.access.platform import AccessPlatform


class TestAWSAccessDomain:
    """Test AWSAccessDomain domain model."""

    def test_create_domain(self):
        """Test creating an AWSAccessDomain."""
        domain = AWSAccessDomain(
            name="test_aws",
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            access_key_secret="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",
        )

        assert domain.name == "test_aws"
        assert domain.platform == AccessPlatform.AWS
        assert domain.access_key_id == "AKIAIOSFODNN7EXAMPLE"
        assert domain.region == "us-east-1"

    def test_domain_platform_is_aws(self):
        """Test that domain platform is AWS."""
        domain = AWSAccessDomain(
            name="test",
            access_key_id="test_key",
        )

        assert domain.platform == AccessPlatform.AWS

    def test_domain_with_session_token(self):
        """Test creating domain with session token."""
        domain = AWSAccessDomain(
            name="test",
            access_key_id="key",
            access_key_secret="secret",
            session_token="token",
        )

        assert domain.session_token == "token"

    def test_domain_with_profile(self):
        """Test creating domain with profile."""
        domain = AWSAccessDomain(
            name="test",
            profile="default",
            region="us-west-2",
        )

        assert domain.profile == "default"
        assert domain.region == "us-west-2"

    def test_domain_with_tags(self):
        """Test creating domain with tags."""
        domain = AWSAccessDomain(
            name="test",
            access_key_id="key",
            tags={"env": "prod", "team": "data"},
        )

        assert domain.tags == {"env": "prod", "team": "data"}


class TestAWSAccess:
    """Test AWSAccess control class."""

    def test_create_access(self):
        """Test creating an AWSAccess instance."""
        access = AWSAccess(
            name="test_aws",
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            access_key_secret="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",
        )

        assert access.name == "test_aws"
        assert access.platform == AccessPlatform.AWS
        assert access.access_key_id == "AKIAIOSFODNN7EXAMPLE"
        assert access.region == "us-east-1"

    def test_access_implements_protocol(self):
        """Test that AWSAccess implements IAccessLike protocol."""
        access = AWSAccess(name="test", access_key_id="key")

        assert isinstance(access, IAccessLike)

    def test_export_masks_credentials(self):
        """Test that export masks sensitive credentials."""
        access = AWSAccess(
            name="test",
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            access_key_secret="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            session_token="FwoGZXIvYXdzEDI",
        )

        exported = access.export()

        assert exported["access_key_id"] == "AKIA******"
        assert exported["access_key_secret"] == "wJal******"
        assert exported["session_token"] == "FwoG******"
        assert exported["name"] == "test"
        assert exported["platform"] == "aws"

    def test_export_handles_none_credentials(self):
        """Test that export handles None credentials."""
        access = AWSAccess(
            name="test",
            profile="default",
        )

        exported = access.export()

        assert exported["access_key_id"] is None
        assert exported["access_key_secret"] is None
        assert exported["session_token"] is None
        assert exported["profile"] == "default"

    def test_roundtrip_from_dict(self):
        """Test roundtrip: dict -> access -> export."""
        data = {
            "name": "test_aws",
            "platform": "aws",
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "access_key_secret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "region": "us-east-1",
            "tags": {"env": "test"},
        }

        access = AWSAccess.from_dict(data)
        exported = access.export()

        assert access.name == "test_aws"
        assert access.platform == AccessPlatform.AWS
        assert exported["name"] == "test_aws"
        assert exported["region"] == "us-east-1"
        assert exported["tags"] == {"env": "test"}

    def test_roundtrip_from_domain(self):
        """Test roundtrip: domain -> access -> domain."""
        domain = AWSAccessDomain(
            name="test_aws",
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            access_key_secret="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-west-2",
            tags={"env": "prod"},
        )

        access = AWSAccess.from_domain(domain)

        assert access.name == "test_aws"
        assert access.access_key_id == "AKIAIOSFODNN7EXAMPLE"
        assert access.region == "us-west-2"
        assert access.tags == {"env": "prod"}

    def test_describe(self):
        """Test describe method returns string representation."""
        access = AWSAccess(
            name="prod_access",
            region="us-east-1",
            account="123456789012",
        )

        description = access.describe()

        assert isinstance(description, str)

    def test_get_fsspec_opts_with_key_and_secret(self):
        """Test get_fsspec_opts returns key and secret for s3fs."""
        access = AWSAccess(
            name="test",
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            access_key_secret="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        )

        opts = access.get_fsspec_opts()

        assert opts == {
            "key": "AKIAIOSFODNN7EXAMPLE",
            "secret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        }

    def test_get_fsspec_opts_with_profile(self):
        """Test get_fsspec_opts returns profile for s3fs."""
        access = AWSAccess(
            name="test",
            profile="default",
        )

        opts = access.get_fsspec_opts()

        assert opts == {"profile": "default"}

    def test_get_fsspec_opts_with_all_params(self):
        """Test get_fsspec_opts returns all s3fs supported params."""
        access = AWSAccess(
            name="test",
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            access_key_secret="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            profile="custom-profile",
        )

        opts = access.get_fsspec_opts()

        assert opts == {
            "key": "AKIAIOSFODNN7EXAMPLE",
            "secret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "profile": "custom-profile",
        }

    def test_get_fsspec_opts_filters_none_values(self):
        """Test get_fsspec_opts filters out None values."""
        access = AWSAccess(
            name="test",
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            # access_key_secret is None
            # profile is None
        )

        opts = access.get_fsspec_opts()

        assert opts == {"key": "AKIAIOSFODNN7EXAMPLE"}
        assert "secret" not in opts
        assert "profile" not in opts

    def test_get_fsspec_opts_with_no_credentials(self):
        """Test get_fsspec_opts returns empty dict when no credentials."""
        access = AWSAccess(name="test")

        opts = access.get_fsspec_opts()

        assert opts == {}

    def test_get_fsspec_opts_excludes_session_token(self):
        """Test get_fsspec_opts does not include session_token (not supported by s3fs)."""
        access = AWSAccess(
            name="test",
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            access_key_secret="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            session_token="FwoGZXIvYXdzEDI",  # This should be excluded
        )

        opts = access.get_fsspec_opts()

        assert "session_token" not in opts
        assert "token" not in opts
        assert opts == {
            "key": "AKIAIOSFODNN7EXAMPLE",
            "secret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        }

    def test_get_fsspec_opts_excludes_region(self):
        """Test get_fsspec_opts does not include region (not part of fsspec opts)."""
        access = AWSAccess(
            name="test",
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            access_key_secret="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",  # This should be excluded
        )

        opts = access.get_fsspec_opts()

        assert "region" not in opts
        assert opts == {
            "key": "AKIAIOSFODNN7EXAMPLE",
            "secret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        }
