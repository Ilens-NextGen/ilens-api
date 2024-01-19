from dataclasses import dataclass, field
from functools import wraps
from logging import getLogger
import sys
import time
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    Optional,
    ParamSpec,
    TypeVar,
    overload,
    Union,
)
import os

T = TypeVar("T", bound=Any)
P = ParamSpec("P")
R = TypeVar("R")
MISSING = object()


def _extract_env_vars(text: str) -> dict[str, str]:
    """Extract environment variables from a string."""
    env_vars = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, value = line.split("=", 1)
        env_vars[name.strip()] = value.strip()
    return env_vars


def loadenv(override: bool = False):
    """Load the environment variables from the env file"""

    if getboolenv("ENV_LOADED", False):
        return
    env_file = getenv("ENV_FILE", ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file) as f:
                env_vars = _extract_env_vars(f.read())
        except Exception as e:
            raise RuntimeError(
                f"Failed to load environment variables from {env_file!r}"
            ) from e
        for name, value in env_vars.items():
            if override or name not in os.environ:
                os.environ[name] = value
            else:
                os.environ.setdefault(name, value)
        os.environ["ENV_LOADED"] = "True"
    else:
        sys.stderr.write(f"Warning: {env_file!r} does not exist.\n")


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


@dataclass
class timed:
    """
    Time operations. can be used as a decorator or context manager.
    Also supports async operations.
    """

    name: Optional[str] = None
    output: Union[str, Callable[[float], str]] = "{name} took: {seconds:0.4f} seconds"
    initial_text: Union[bool, str] = False
    interrupt_output: Union[
        str, Callable[[float], str]
    ] = "{name} interrupted after {:0.4f} seconds"
    logger: Optional[Callable[[str], Any]] = field(
        default_factory=lambda: getLogger("timer").info
    )

    def start(self):
        """Start the timer."""
        self._start = time.perf_counter()
        if self.logger and self.initial_text:
            if isinstance(self.initial_text, str):
                initial_text = self.initial_text.format(name=self.name)
            elif self.name:
                initial_text = f"{self.name} started"
            else:
                initial_text = "Operation started"
            self.logger(initial_text)

    def interrupt(self):
        """Interrupt the timer."""
        self._end = time.perf_counter()
        self._interval = self._end - self._start
        if self.logger:
            if callable(self.interrupt_output):
                self.logger(self.interrupt_output(self._interval))
            else:
                self.logger(
                    self.interrupt_output.format(name=self.name, seconds=self._interval)
                )

    def stop(self):
        """Stop the timer."""
        self._end = time.perf_counter()
        self._interval = self._end - self._start
        if self.logger:
            if callable(self.output):
                self.logger(self.output(self._interval))
            else:
                self.logger(self.output.format(name=self.name, seconds=self._interval))

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.interrupt()
        else:
            self.stop()
        return False

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_value, traceback):
        return self.__exit__(exc_type, exc_value, traceback)

    def __call__(self, func: Callable[P, R]) -> Callable[P, R]:
        if not self.name:
            self.name = func.__qualname__

        @wraps(func)
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

    @classmethod
    def async_(cls, *args, **kwargs):
        timer = cls(*args, **kwargs)
        return timer.async_decorator

    def async_decorator(
        self, func: Callable[P, Awaitable[R]]
    ) -> Callable[P, Awaitable[R]]:
        if not self.name:
            self.name = func.__qualname__

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs):
            self.start()
            try:
                result = await func(*args, **kwargs)
                self.stop()
                return result
            except Exception as e:
                self.interrupt()
                raise e

        return wrapper
