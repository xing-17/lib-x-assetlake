"""Unit tests for Aliyun access."""

from __future__ import annotations

from assetlake.control.access.aliyun import AliyunAccess, AliyunAccessDomain
from assetlake.control.access.base.protocol import IAccessLike
from assetlake.domain.access.platform import AccessPlatform


class TestAliyunAccessDomain:
    """Test AliyunAccessDomain domain model."""

    def test_create_domain(self):
        """Test creating an AliyunAccessDomain."""
        domain = AliyunAccessDomain(
            name="test_aliyun",
            access_key_id="LTAI4GBcXXXXXXXXXXXX",
            access_key_secret="xxxxxxxxxxxxxxxxxxxxx",
        )

        assert domain.name == "test_aliyun"
        assert domain.platform == AccessPlatform.ALIYUN
        assert domain.access_key_id == "LTAI4GBcXXXXXXXXXXXX"

    def test_domain_platform_is_aliyun(self):
        """Test that domain platform is ALIYUN."""
        domain = AliyunAccessDomain(
            name="test",
            access_key_id="test_key",
        )

        assert domain.platform == AccessPlatform.ALIYUN

    def test_domain_with_tags(self):
        """Test creating domain with tags."""
        domain = AliyunAccessDomain(
            name="test",
            access_key_id="key",
            tags={"env": "prod", "team": "data"},
        )

        assert domain.tags == {"env": "prod", "team": "data"}


class TestAliyunAccess:
    """Test AliyunAccess control class."""

    def test_create_access(self):
        """Test creating an AliyunAccess instance."""
        access = AliyunAccess(
            name="test_aliyun",
            access_key_id="LTAI4GBcXXXXXXXXXXXX",
            access_key_secret="xxxxxxxxxxxxxxxxxxxxx",
        )

        assert access.name == "test_aliyun"
        assert access.platform == AccessPlatform.ALIYUN
        assert access.access_key_id == "LTAI4GBcXXXXXXXXXXXX"

    def test_access_implements_protocol(self):
        """Test that AliyunAccess implements IAccessLike protocol."""
        access = AliyunAccess(name="test", access_key_id="key")

        assert isinstance(access, IAccessLike)

    def test_export_masks_credentials(self):
        """Test that export masks sensitive credentials."""
        access = AliyunAccess(
            name="test",
            access_key_id="LTAI4GBcXXXXXXXXXXXX",
            access_key_secret="xxxxxxxxxxxxxxxxxxxxx",
        )

        exported = access.export()
        assert exported["access_key_id"] == "LTAI******"
        assert exported["access_key_secret"] == "xxxx******"
        assert exported["name"] == "test"
        assert exported["platform"] == "aliyun"

    def test_export_handles_none_credentials(self):
        """Test that export handles None credentials."""
        access = AliyunAccess(
            name="test",
        )

        exported = access.export()

        assert exported["access_key_id"] is None
        assert exported["access_key_secret"] is None

    def test_roundtrip_from_dict(self):
        """Test roundtrip: dict -> access -> export."""
        data = {
            "name": "test_aliyun",
            "platform": "aliyun",
            "access_key_id": "LTAI4GBcXXXXXXXXXXXX",
            "access_key_secret": "xxxxxxxxxxxxxxxxxxxxx",
            "tags": {"env": "test"},
        }

        access = AliyunAccess.from_dict(data)
        exported = access.export()

        assert access.name == "test_aliyun"
        assert access.platform == AccessPlatform.ALIYUN
        assert exported["name"] == "test_aliyun"
        assert exported["tags"] == {"env": "test"}

    def test_roundtrip_from_domain(self):
        """Test roundtrip: domain -> access -> domain."""
        domain = AliyunAccessDomain(
            name="test_aliyun",
            access_key_id="LTAI4GBcXXXXXXXXXXXX",
            access_key_secret="xxxxxxxxxxxxxxxxxxxxx",
            tags={"env": "prod"},
        )

        access = AliyunAccess.from_domain(domain)

        assert access.name == "test_aliyun"
        assert access.access_key_id == "LTAI4GBcXXXXXXXXXXXX"
        assert access.tags == {"env": "prod"}

    def test_describe(self):
        """Test describe method returns string representation."""
        access = AliyunAccess(
            name="prod_access",
            access_key_id="LTAI4GBcXXXXXXXXXXXX",
        )

        description = access.describe()

        assert isinstance(description, str)
        assert len(description) > 0
