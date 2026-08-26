"""Unit tests for IDomain."""

from __future__ import annotations

from typing import Optional

from assetlake.internal.idomain import IDomain


class TestModel(IDomain):
    """Test model with custom prefix."""

    __test__ = False
    _id_prefix = "test"
    name: str = "default"


class TestModelNoPrefix(IDomain):
    """Test model without prefix."""

    __test__ = False
    _id_prefix = ""
    value: int = 0


class NestedModel(IDomain):
    """Nested model for complex structure tests."""

    __test__ = False
    _id_prefix = "nested"
    title: str
    count: int = 0


class ComplexModel(IDomain):
    """Model with complex data structures."""

    __test__ = False
    _id_prefix = "complex"
    name: str
    tags: list[str] = []
    metadata: dict[str, str] = {}
    nested: Optional[NestedModel] = None
    numbers: list[int] = []


class ModelWithOptionalFields(IDomain):
    """Model with various optional field configurations."""

    __test__ = False
    _id_prefix = "opt"
    required_field: str
    optional_with_none: Optional[str] = None
    optional_without_default: Optional[str] = None
    field_with_default: str = "default_value"
    optional_int: Optional[int] = None
    optional_list: Optional[list[str]] = None


class ModelWithNoneAccepting(IDomain):
    """Model specifically for testing None value handling."""

    __test__ = False
    _id_prefix = "none"
    accepts_none: Optional[str] = None
    has_default_no_none: str = "default"
    accepts_none_with_default: Optional[str] = "default"


def test_auto_id_generation():
    """Test that ID is auto-generated on initialization."""
    model = TestModel(name="example")
    assert model.id
    assert model.id.startswith("test-")
    assert len(model.id.split("-")[1]) == 12


def test_auto_id_generation_no_prefix():
    """Test ID generation without prefix."""
    model = TestModelNoPrefix(value=42)
    assert model.id
    assert "-" not in model.id
    assert len(model.id) == 12


def test_custom_id():
    """Test providing a custom ID."""
    custom_id = "custom-123"
    model = TestModel(id=custom_id, name="example")
    assert model.id == custom_id


def test_from_dict():
    """Test creating model from JSON dictionary."""
    data = {"id": "test-abc123", "name": "from_dict"}
    model = TestModel.from_dict(data)
    assert model.id == "test-abc123"
    assert model.name == "from_dict"


def test_export():
    """Test exporting model to dictionary."""
    model = TestModel(name="export_test")
    exported = model.export()
    assert isinstance(exported, dict)
    assert "id" in exported
    assert "name" in exported
    assert exported["name"] == "export_test"


def test_describe():
    """Test JSON string representation."""
    model = TestModel(name="describe_test")
    description = model.describe()
    assert isinstance(description, str)
    assert "describe_test" in description
    assert "id" in description


def test_extra_fields_ignored():
    """Test that extra fields are ignored."""
    data = {"name": "test", "extra_field": "ignored"}
    model = TestModel.from_dict(data)
    assert model.name == "test"
    assert not hasattr(model, "extra_field")


def test_validate_assignment():
    """Test that assignment validation works."""
    model = TestModel(name="initial")
    model.name = "updated"
    assert model.name == "updated"


# ============================================================================
# Complex Data Structure Tests
# ============================================================================


def test_complex_nested_structure():
    """Test model with nested objects."""
    nested = NestedModel(title="Nested Item", count=5)
    complex_model = ComplexModel(
        name="Complex",
        tags=["tag1", "tag2", "tag3"],
        metadata={"key1": "value1", "key2": "value2"},
        nested=nested,
        numbers=[1, 2, 3, 4, 5],
    )

    assert complex_model.name == "Complex"
    assert len(complex_model.tags) == 3
    assert complex_model.metadata["key1"] == "value1"
    assert complex_model.nested is not None
    assert complex_model.nested.title == "Nested Item"
    assert complex_model.nested.count == 5
    assert complex_model.numbers == [1, 2, 3, 4, 5]
    assert complex_model.id.startswith("complex-")
    assert complex_model.nested.id.startswith("nested-")


def test_complex_structure_with_empty_collections():
    """Test complex model with empty collections."""
    model = ComplexModel(name="Empty Collections")

    assert model.name == "Empty Collections"
    assert model.tags == []
    assert model.metadata == {}
    assert model.nested is None
    assert model.numbers == []
    assert model.id.startswith("complex-")


def test_deeply_nested_structure():
    """Test deeply nested object structures."""
    # Create a chain of nested models
    inner_nested = NestedModel(title="Inner", count=1)
    middle_model = ComplexModel(
        name="Middle",
        nested=inner_nested,
        tags=["middle"],
    )

    # Export and re-import to test serialization
    middle_dict = middle_model.export()
    middle_dict["nested_complex"] = middle_dict  # Add self-reference to dict

    # Create outer model
    outer = ComplexModel(
        name="Outer",
        tags=["outer"],
        metadata={"layer": "top"},
        numbers=[10, 20, 30],
    )

    assert outer.name == "Outer"
    assert outer.id.startswith("complex-")


# ============================================================================
# Roundtrip Tests (export -> from_dict)
# ============================================================================


def test_simple_roundtrip():
    """Test export and re-import preserves data."""
    original = TestModel(name="roundtrip_test")
    exported = original.export()
    restored = TestModel.from_dict(exported)

    assert restored.id == original.id
    assert restored.name == original.name


def test_complex_roundtrip():
    """Test roundtrip with complex nested structures."""
    nested = NestedModel(title="Roundtrip Nested", count=42)
    original = ComplexModel(
        name="Roundtrip Complex",
        tags=["a", "b", "c"],
        metadata={"foo": "bar", "baz": "qux"},
        nested=nested,
        numbers=[100, 200, 300],
    )

    # Export to dict
    exported = original.export()

    # Verify exported structure
    assert isinstance(exported, dict)
    assert exported["name"] == "Roundtrip Complex"
    assert exported["tags"] == ["a", "b", "c"]
    assert isinstance(exported["nested"], dict)
    assert exported["nested"]["title"] == "Roundtrip Nested"

    # Re-import from dict
    restored = ComplexModel.from_dict(exported)

    # Verify all fields match
    assert restored.id == original.id
    assert restored.name == original.name
    assert restored.tags == original.tags
    assert restored.metadata == original.metadata
    assert restored.numbers == original.numbers
    assert restored.nested is not None
    assert restored.nested.id == original.nested.id
    assert restored.nested.title == original.nested.title
    assert restored.nested.count == original.nested.count


def test_roundtrip_with_none_values():
    """Test roundtrip when optional fields are None."""
    original = ComplexModel(name="None Test", nested=None)

    exported = original.export()
    restored = ComplexModel.from_dict(exported)

    assert restored.id == original.id
    assert restored.name == original.name
    assert restored.nested is None
    assert restored.tags == []
    assert restored.metadata == {}


def test_multiple_roundtrips():
    """Test multiple export/import cycles preserve data integrity."""
    original = ComplexModel(
        name="Multi Roundtrip",
        tags=["persistent"],
        metadata={"cycle": "test"},
        numbers=[1, 2, 3],
    )

    current = original
    for i in range(5):
        exported = current.export()
        current = ComplexModel.from_dict(exported)

        # Verify data integrity after each cycle
        assert current.name == "Multi Roundtrip"
        assert current.tags == ["persistent"]
        assert current.metadata == {"cycle": "test"}
        assert current.numbers == [1, 2, 3]


# ============================================================================
# None Value and Default Handling Tests
# ============================================================================


def test_none_value_passed_explicitly_with_optional():
    """Test passing None explicitly to optional field."""
    # When None is passed explicitly and field accepts None, it should be None
    model = ModelWithOptionalFields(
        required_field="required",
        optional_with_none=None,
    )

    assert model.required_field == "required"
    assert model.optional_with_none is None
    assert model.optional_without_default is None
    assert model.field_with_default == "default_value"


def test_none_value_in_dict_with_optional():
    """Test from_dict with explicit None values."""
    data = {
        "required_field": "required",
        "optional_with_none": None,
        "optional_int": None,
    }
    model = ModelWithOptionalFields.from_dict(data)

    assert model.required_field == "required"
    assert model.optional_with_none is None
    assert model.optional_int is None
    assert model.field_with_default == "default_value"


def test_none_value_with_default_non_optional():
    """Test None handling for fields with defaults that don't accept None."""
    # Field has default but doesn't accept None - None should trigger default
    data = {
        "required_field": "required",
        "field_with_default": None,  # This should use default
    }
    model = ModelWithOptionalFields.from_dict(data)

    # The None should be removed and default should be used
    assert model.field_with_default == "default_value"


def test_field_not_passed_uses_default():
    """Test that fields not passed use their defaults."""
    model = ModelWithOptionalFields(required_field="only_required")

    assert model.required_field == "only_required"
    assert model.optional_with_none is None
    assert model.optional_without_default is None
    assert model.field_with_default == "default_value"
    assert model.optional_int is None
    assert model.optional_list is None


def test_none_accepting_fields():
    """Test various combinations of None acceptance and defaults."""
    # Test with all None
    model1 = ModelWithNoneAccepting(
        accepts_none=None,
        has_default_no_none=None,  # Should use default
        accepts_none_with_default=None,
    )
    assert model1.accepts_none is None
    assert model1.has_default_no_none == "default"  # Default used
    assert model1.accepts_none_with_default is None

    # Test with values
    model2 = ModelWithNoneAccepting(
        accepts_none="value",
        has_default_no_none="custom",
        accepts_none_with_default="custom",
    )
    assert model2.accepts_none == "value"
    assert model2.has_default_no_none == "custom"
    assert model2.accepts_none_with_default == "custom"


def test_optional_list_with_none():
    """Test optional list field with None vs empty list."""
    # None explicitly passed
    model1 = ModelWithOptionalFields(
        required_field="test",
        optional_list=None,
    )
    assert model1.optional_list is None

    # Empty list passed
    model2 = ModelWithOptionalFields(
        required_field="test",
        optional_list=[],
    )
    assert model2.optional_list == []
    assert isinstance(model2.optional_list, list)

    # List with values
    model3 = ModelWithOptionalFields(
        required_field="test",
        optional_list=["a", "b"],
    )
    assert model3.optional_list == ["a", "b"]


# ============================================================================
# Clone and Modification Tests
# ============================================================================


def test_clone_simple():
    """Test cloning a simple model."""
    original = TestModel(name="original")
    cloned = original.clone()

    assert cloned.id == original.id
    assert cloned.name == original.name
    assert cloned is not original  # Different object


def test_clone_with_updates():
    """Test cloning with field updates."""
    original = TestModel(name="original")
    cloned = original.clone(name="cloned")

    assert cloned.id == original.id  # ID preserved
    assert cloned.name == "cloned"  # Name updated
    assert original.name == "original"  # Original unchanged


def test_clone_complex_structure():
    """Test cloning complex nested structures."""
    nested = NestedModel(title="Original Nested", count=10)
    original = ComplexModel(
        name="Original",
        tags=["tag1", "tag2"],
        metadata={"key": "value"},
        nested=nested,
        numbers=[1, 2, 3],
    )

    cloned = original.clone()

    # Verify deep copy
    assert cloned is not original
    assert cloned.nested is not original.nested
    assert cloned.tags is not original.tags
    assert cloned.metadata is not original.metadata
    assert cloned.numbers is not original.numbers

    # Verify values match
    assert cloned.name == original.name
    assert cloned.tags == original.tags
    assert cloned.nested.title == original.nested.title

    # Modify cloned - should not affect original
    cloned.tags.append("tag3")
    cloned.metadata["new_key"] = "new_value"

    assert len(original.tags) == 2
    assert "new_key" not in original.metadata


def test_clone_with_nested_update():
    """Test cloning with updates to nested fields."""
    nested = NestedModel(title="Original", count=5)
    original = ComplexModel(name="Original", nested=nested)

    new_nested = NestedModel(title="Updated", count=10)
    cloned = original.clone(nested=new_nested)

    assert cloned.name == original.name
    assert cloned.nested.title == "Updated"
    assert cloned.nested.count == 10
    assert original.nested.title == "Original"
    assert original.nested.count == 5


# ============================================================================
# SHA256 Hash Tests
# ============================================================================


def test_sha256_consistency():
    """Test that sha256 hash is consistent for same data."""
    model = TestModel(id="fixed-id", name="test")
    hash1 = model.sha256
    hash2 = model.sha256

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 produces 64 hex characters


def test_sha256_changes_with_data():
    """Test that sha256 changes when data changes."""
    model = TestModel(id="fixed-id", name="test1")
    hash1 = model.sha256

    model.name = "test2"
    hash2 = model.sha256

    assert hash1 != hash2


def test_sha256_same_for_equal_models():
    """Test that equal models have the same hash."""
    model1 = TestModel(id="fixed-id", name="test")
    model2 = TestModel(id="fixed-id", name="test")

    assert model1.sha256 == model2.sha256


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


def test_from_dict_with_existing_instance():
    """Test from_dict when passed an existing instance."""
    original = TestModel(name="original")
    result = TestModel.from_dict(original)

    assert result is original  # Should return the same instance


def test_empty_string_id_generates_new():
    """Test that empty string ID triggers generation."""
    model = TestModel(id="", name="test")
    assert model.id != ""
    assert model.id.startswith("test-")


def test_large_data_structure():
    """Test handling of large data structures."""
    large_tags = [f"tag_{i}" for i in range(1000)]
    large_metadata = {f"key_{i}": f"value_{i}" for i in range(1000)}
    large_numbers = list(range(10000))

    model = ComplexModel(
        name="Large",
        tags=large_tags,
        metadata=large_metadata,
        numbers=large_numbers,
    )

    # Test export and roundtrip
    exported = model.export()
    restored = ComplexModel.from_dict(exported)

    assert len(restored.tags) == 1000
    assert len(restored.metadata) == 1000
    assert len(restored.numbers) == 10000
    assert restored.tags[999] == "tag_999"
    assert restored.metadata["key_999"] == "value_999"


def test_describe_format():
    """Test that describe returns properly formatted JSON."""
    model = ComplexModel(
        name="Describe Test",
        tags=["a", "b"],
        metadata={"key": "value"},
    )

    description = model.describe()

    assert isinstance(description, str)
    assert '"name": "Describe Test"' in description
    assert '"tags"' in description
    assert '"metadata"' in description
    # Check that it's indented (pretty printed)
    assert "    " in description


def test_id_prefix_variations():
    """Test various ID prefix configurations."""
    # With prefix
    model1 = TestModel(name="test")
    assert "-" in model1.id
    assert model1.id.startswith("test-")

    # Without prefix
    model2 = TestModelNoPrefix(value=1)
    assert "-" not in model2.id

    # Nested model
    model3 = NestedModel(title="nested")
    assert model3.id.startswith("nested-")


def test_model_immutability_after_export():
    """Test that export doesn't affect the model state."""
    model = ComplexModel(
        name="Immutable",
        tags=["tag1"],
        metadata={"key": "value"},
    )

    original_name = model.name
    original_tags = model.tags.copy()
    original_metadata = model.metadata.copy()

    # Export multiple times
    for _ in range(3):
        exported = model.export()
        # Modify exported dict
        exported["name"] = "Modified"
        exported["tags"].append("new_tag")

    # Model should remain unchanged
    assert model.name == original_name
    assert model.tags == original_tags
    assert model.metadata == original_metadata
