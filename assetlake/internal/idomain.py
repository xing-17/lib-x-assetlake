from __future__ import annotations

import hashlib
import uuid
from typing import ClassVar, Self, get_args

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)
from pydantic_core import PydanticUndefined


class IDomain(BaseModel):
    """
    Base Pydantic model with auto-generated ID and serialization utilities.

    Attributes:
        id (str): Unique identifier for the model instance, auto-generated if not provided.
        _id_enabled (ClassVar[bool]): Whether to enable auto-generated IDs.
        _id_prefix (ClassVar[str]): Prefix for auto-generated IDs.
        _id_length (ClassVar[int]): Length of the generated UUID portion.

    Methods:
        from_dict(dict | Self value): Create instance from dict or existing instance.
        clone(**updates): Create a deep copy with optional field updates.
        export(): Export the model instance to a JSON-serializable dictionary.
        describe(): Return a JSON string representation of the model.
        logic_name: Property returning a formatted name with class and ID.

    """

    _id_enabled: ClassVar[bool] = True
    _id_prefix: ClassVar[str] = ""
    _id_length: ClassVar[int] = 12
    id: str = Field(
        default="",
        description="Unique identifier for the model instance",
    )
    model_config = ConfigDict(
        frozen=False,
        extra="ignore",
        validate_assignment=True,
        populate_by_name=True,
    )

    @classmethod
    def from_dict(
        cls,
        value: dict | Self,
    ) -> Self:
        if isinstance(value, cls):
            return value
        return cls.model_validate(value)

    @model_validator(mode="before")
    @classmethod
    def _prepare(cls, data):
        if isinstance(data, dict):
            # avoid mutating the original dict
            data = dict(data)

            for name, field_info in cls.model_fields.items():
                if name not in data:
                    continue
                if data[name] is not None:
                    continue

                # Check if fields has a default value or default factory
                _has_default = (
                    field_info.default is not PydanticUndefined
                    or field_info.default_factory is not None
                )
                # Check if the field accepts None
                _accepts_none = type(None) in get_args(field_info.annotation)

                # Only remove the field if it has a default and does not accept None
                if _has_default and not _accepts_none:
                    del data[name]

            # Generate an ID if it's enabled and not provided
            if cls._id_enabled and not data.get("id"):
                data["id"] = cls._generate_id()

        return data

    @classmethod
    def _generate_id(cls) -> str:
        prefix = cls._id_prefix
        value = uuid.uuid4().hex[: cls._id_length]
        return f"{prefix}-{value}" if prefix else value

    @property
    def sha256(self) -> str:
        _string = self.model_dump_json(
            indent=4,
            ensure_ascii=False,
        )
        _value = hashlib.sha256(_string.encode("utf-8")).hexdigest()
        return _value

    def clone(
        self,
        **updates,
    ) -> Self:
        return self.model_copy(
            update=updates,
            deep=True,
        )

    def export(self) -> dict:
        return self.model_dump(
            mode="json",
            round_trip=True,
        )

    def describe(self) -> str:
        return self.model_dump_json(
            indent=4,
            ensure_ascii=False,
        )
