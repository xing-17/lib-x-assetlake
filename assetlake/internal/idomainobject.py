from __future__ import annotations

from typing import Any, ClassVar, Self

from assetlake.internal.idomain import IDomain


class IDomainObject:
    """
    Base wrapper class for domain models with attribute delegation.

    Attributes:
        _domain_class (ClassVar[type[IDomain] | None]): The domain model class to wrap.
        domain (IDomain): The underlying domain model instance.

    Methods:
        from_dict(dict data): Create instance from dictionary data.
        from_domain(IBastionModel domain): Create instance from domain model.
        export(): Export the underlying domain model to a dictionary.
        describe(): Return a JSON string representation of the domain model.

    """

    _domain_class: ClassVar[type[IDomain] | None] = None

    def __init__(
        self,
        **kwargs,
    ) -> None:
        if kwargs:
            if self._domain_class is None:
                _klass = self.__class__.__name__
                raise TypeError(f"{_klass} has no _domain_class")
            self.domain = self._domain_class(**kwargs)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, str | dict],
    ) -> Self:
        if cls._domain_class is None:
            _klass = cls.__name__
            raise TypeError(f"{_klass} has no _domain_class")
        domain = cls._domain_class.from_dict(data)
        return cls.from_domain(domain)

    @classmethod
    def from_domain(
        cls,
        domain: IDomain,
    ) -> Self:
        obj = cls.__new__(cls)
        object.__init__(obj)
        obj.domain = domain
        return obj

    def __getattr__(
        self,
        name: str,
    ) -> Any:
        domain = self.__dict__.get("domain")
        if domain is not None:
            return getattr(domain, name)
        _klass = self.__class__.__name__
        raise AttributeError(f"'{_klass}' has no attribute '{name}'")

    def export(self) -> dict:
        return self.domain.export()

    def describe(self) -> str:
        return self.domain.describe()
