from dataclasses import dataclass, field
from typing import Any, Callable, Generic, TypeVar, overload, Union
import os

T = TypeVar("T", bound=Any)
MISSING = object()


@overload
def getenv(name: str) -> str:
    ...


@overload
def getenv(name: str, default: T) -> Union[str, T]:
    ...


def getenv(name: str, default: Union[str, T] = MISSING) -> Union[str, T]:  # type: ignore[assignment]
    """Get environment variable or return default value."""
    try:
        return os.environ[name]
    except KeyError:
        if default is MISSING:
            raise RuntimeError(f"Environment variable {name!r} is not set.") from None
        return default


@overload
def getlistenv(name: str) -> list[str]:
    ...


@overload
def getlistenv(name: str, default: T) -> Union[list[str], T]:
    ...


def getlistenv(name: str, default: Union[list[str], T] = MISSING) -> Union[list[str], T]:  # type: ignore[assignment]
    """Get environment variable or return default value."""
    try:
        return os.environ[name].split(",")
    except KeyError:
        if default is MISSING:
            raise RuntimeError(f"Environment variable {name!r} is not set.") from None
        return default


@overload
def getintenv(name: str) -> int:
    ...


@overload
def getintenv(name: str, default: T) -> Union[int, T]:
    ...


def getintenv(name: str, default: Union[int, T] = MISSING) -> Union[int, T]:  # type: ignore[assignment]
    """Get environment variable or return default value."""
    try:
        return int(os.environ[name])
    except KeyError:
        if default is MISSING:
            raise RuntimeError(f"Environment variable {name!r} is not set.") from None
        return default


@overload
def getfloatenv(name: str) -> float:
    ...


@overload
def getfloatenv(name: str, default: T) -> Union[float, T]:
    ...


def getfloatenv(name: str, default: Union[float, T] = MISSING) -> Union[float, T]:  # type: ignore[assignment]
    """Get environment variable or return default value."""
    try:
        return float(os.environ[name])
    except KeyError:
        if default is MISSING:
            raise RuntimeError(f"Environment variable {name!r} is not set.") from None
        return default


@overload
def getboolenv(name: str) -> bool:
    ...


@overload
def getboolenv(name: str, default: T) -> Union[bool, T]:
    ...


def getboolenv(name: str, default: Union[bool, T] = MISSING) -> Union[bool, T]:  # type: ignore[assignment]
    """Get environment variable or return default value."""
    try:
        return os.environ[name].lower() in ["true", "1", "yes"]
    except KeyError:
        if default is MISSING:
            raise RuntimeError(f"Environment variable {name!r} is not set.") from None
        return default


@dataclass
class EnvDescriptor(Generic[T]):
    """Descriptor for environment variables."""

    name: str
    default: T = MISSING  # type: ignore[assignment]
    getter: Callable[[str, T], Union[str, T]] = field(repr=False, init=False)
    _value: T = field(init=False, repr=False)

    def __get__(self, instance, type):
        if instance is None:
            return self
        if getattr(self, "_value", MISSING) is MISSING:
            val = self.getter(self.name, self.default)
            setattr(self, "_value", val)
            return val
        return getattr(self, "_value")

    def __set__(self, instance, value):
        setattr(self, "_value", value)

    def __delete__(self, instance):
        delattr(self, "_value")


@overload
def env_descriptor(name: str) -> str:
    ...


@overload
def env_descriptor(name: str, default: T) -> Union[str, T]:
    ...


@overload
def env_descriptor(name: str, default: T, getter: Callable[[str, T], T]) -> T:
    ...


def env_descriptor(
    name: str,
    default: T = MISSING,  # type: ignore[assignment]
    getter: Callable[[str, T], T] = getenv,  # type: ignore[assignment]
) -> T:
    """
    Create a descriptor for environment variables.

    This should be used directly as a class attribute.


    Example:
    ```py
        class Foo:
            bar = env_descriptor("BAR", "baz")
    ```

    Args:
        name (str): Name of the environment variable.
        default (Any, optional): Default value if the environment variable is not set.
    Raises:
        RuntimeError: If the environment variable is not set and no default value is provided.
    """
    descriptor = EnvDescriptor(name, default)
    descriptor.getter = getter
    return descriptor  # type: ignore[return-value]
