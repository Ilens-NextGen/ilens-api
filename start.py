#!/usr/bin/env python3

from typing import Any, Optional
from server.utils import getboolenv, getenv, getintenv, getlistenv, loadenv
import sys
from sanic.__main__ import main as sanic  # noqa: F401


def main() -> Optional[int]:
    loadenv()
    args: dict[str, Any] = {}

    # Application
    args["--factory"] = getenv("SANIC_FACTORY", False)
    args["--simple"] = getboolenv("SANIC_SIMPLE", False)
    args["--repl"] = getboolenv("SANIC_REPL", False)
    # HTTP version
    args["--http"] = getintenv("SANIC_HTTP", None)
    args["-1"] = getboolenv("SANIC_HTTP_1", False)
    args["-3"] = getboolenv("SANIC_HTTP_3", False)

    # Socket binding
    args["--host"] = getenv("HOST", "0.0.0.0")
    args["--port"] = getintenv("PORT", 8000)
    args["--unix"] = getenv("UNIX", None)

    # TSL certificate
    args["--cert"] = getenv("CERT", None)
    args["--key"] = getenv("KEY", None)
    args["--tls"] = getlistenv("TLS", [])
    args["--tls-strict-host"] = getboolenv("TLS_STRICT_HOST", False)

    # Worker
    args["--workers"] = getintenv("SANIC_WORKERS", 1)
    args["--fast"] = getboolenv("SANIC_FAST", False)
    args["--single-process"] = getboolenv("SANIC_SINGLE_PROCESS", False)
    args["--access-logs"] = getboolenv("SANIC_ACCESS_LOGS", True)

    # Development
    args["--dev"] = getboolenv("SANIC_DEV", getboolenv("DEBUG", False))
    args["--reload"] = getboolenv("SANIC_RELOAD", getboolenv("DEBUG", False))
    args["--reload-dir"] = getenv("SANIC_RELOAD_DIR", None)
    args["--auto-tls"] = getboolenv("SANIC_AUTO_TLS", False)

    # Output
    args["--motd"] = getboolenv("SANIC_MOTD", True)
    args["--noisy-exceptions"] = getboolenv("SANIC_NOISY_EXCEPTIONS", False)
    args["--verbosity"] = getintenv("SANIC_VERBOSITY", None)

    target = getenv("ASGI_APPLICATION")

    # build args
    cli_args: list[str] = []

    for arg, value in args.items():
        if value is None:
            continue
        if isinstance(value, bool):
            if value:
                cli_args.append(arg)
        elif isinstance(value, int):
            cli_args.extend([arg, str(value)])
        elif isinstance(value, str):
            cli_args.extend([arg, value])
        elif isinstance(value, list):
            for item in value:
                cli_args.extend([arg, item])
        else:
            raise TypeError(f"Unexpected type {type(value)} for {arg}={value!r}")

    cli_args.append(target)
    sys.argv.extend(cli_args)
    print(f"Executing: {' '.join(sys.argv)}")
    return sanic()


if __name__ == "__main__":
    exit(main())
