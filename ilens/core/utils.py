from dataclasses import dataclass, field
import time
from typing import Any, Callable, Generic, Optional, ParamSpec, TypeVar, overload, Union
import os

T = TypeVar("T", bound=Any)
P = ParamSpec("P")
R = TypeVar("R")
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


class timed:
    """
    Time operations. can be used as a decorator or context manager.
    """

    debug = env_descriptor("DEBUG", False, getboolenv)

    def __init__(
        self, op_name: Optional[str] = None, writer: Callable[[str], Any] = print
    ):
        """Initialize the timed object.

        Args:
            op_name (Optional[str], optional): Name of the operation. Defaults to None.
            writer (Callable[[str], Any], optional): Writer function. Defaults to print.
        """
        self.op_name = op_name
        self.writer = writer

    def start(self):
        """Start the timer."""
        self._start = time.perf_counter()
        self.debug and self.writer(f"`{self.op_name or 'Operation'}` started")

    def interrupt(self):
        """Interrupt the timer."""
        self._end = time.perf_counter()
        self._interval = self._end - self._start
        self.debug and self.writer(
            f"`{self.op_name or 'Operation'}` interrupted after {self._interval:.3f} seconds"
        )

    def stop(self):
        """Stop the timer."""
        self._end = time.perf_counter()
        self._interval = self._end - self._start
        self.debug and self.writer(
            f"`{self.op_name or 'Operation'}` took {self._interval:.3f} seconds"
        )

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.interrupt()
        else:
            self.stop()
        return False

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        if not self.op_name:
            self.op_name = func.__qualname__

        def wrapper(*args: P.args, **kwargs: P.kwargs):
            self.start()
            try:
                result = func(*args, **kwargs)
                self.stop()
                return result
            except Exception as e:
                self.interrupt()
                raise e

        return wrapper
