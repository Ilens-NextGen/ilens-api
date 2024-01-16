#!/usr/bin/env python3

import daphne.cli  # type: ignore[import]
from ilens.core.utils import getenv, getintenv, getlistenv
import argparse


class CommandLineInterface(daphne.cli.CommandLineInterface):
    description = "iLens HTTP/WebSocket server"

    def __init__(self):
        self.parser = argparse.ArgumentParser(description=self.description)
        self.parser.add_argument(
            "-p",
            "--port",
            type=int,
            help="Port number to listen on",
            default=getenv("PORT", None),
        )
        self.parser.add_argument(
            "-b",
            "--bind",
            dest="host",
            help="The host/address to bind to",
            default=getenv("HOST", None),
        )
        self.parser.add_argument(
            "--websocket-timeout",
            type=int,
            dest="websocket_timeout",
            help="Maximum time to allow a websocket to be connected. -1 for infinite.",
            default=getintenv("WEBSOCKET_TIMEOUT", -1),
        )
        self.parser.add_argument(
            "--websocket-connect-timeout",
            dest="websocket_connect_timeout",
            type=int,
            help="Maximum time to allow a connection to handshake. -1 for infinite",
            default=getintenv("WEBSOCKET_CONNECT_TIMEOUT", 5),
        )
        self.parser.add_argument(
            "-u",
            "--unix-socket",
            dest="unix_socket",
            help="Bind to a UNIX socket rather than a TCP host/port",
            default=getenv("UNIX_SOCKET", None),
        )
        self.parser.add_argument(
            "--fd",
            type=int,
            dest="file_descriptor",
            help="Bind to a file descriptor rather than a TCP host/port or named unix socket",
            default=getintenv("FILE_DESCRIPTOR", None),
        )
        self.parser.add_argument(
            "-e",
            "--endpoint",
            dest="socket_strings",
            help="Use raw server strings passed directly to twisted",
            default=getlistenv("SOCKET_STRINGS", []),
        )
        self.parser.add_argument(
            "-v",
            "--verbosity",
            type=int,
            help="How verbose to make the output",
            default=getintenv("VERBOSITY", 1),
        )
        self.parser.add_argument(
            "-t",
            "--http-timeout",
            type=int,
            dest="http_timeout",
            help="How long to wait for HTTP responses, in seconds",
            default=getintenv("HTTP_TIMEOUT", 5),
        )
        self.parser.add_argument(
            "--access-log",
            help="Where to write the access log (- for stdout, the default for verbosity=1)",
            default=getenv("ACCESS_LOG", None),
        )
        self.parser.add_argument(
            "--log-fmt",
            help="Python logger format string to use",
            default=getenv("LOG_FMT", "%(asctime)-15s %(levelname)-8s %(message)s"),
        )
        self.parser.add_argument(
            "--ping-interval",
            type=int,
            help="The number of seconds a WebSocket must be idle before a keepalive ping is sent",
            default=getintenv("PING_INTERVAL", 20),
        )
        self.parser.add_argument(
            "--ping-timeout",
            type=int,
            help="The number of seconds before a WebSocket is closed if no response to a keepalive ping",
            default=getintenv("PING_TIMEOUT", 20),
        )
        self.parser.add_argument(
            "--application-close-timeout",
            type=int,
            help="The number of seconds an ASGI application has to exit after client disconnect before it is killed",
            default=getintenv("APPLICATION_CLOSE_TIMEOUT", 10),
        )
        self.parser.add_argument(
            "--root-path",
            dest="root_path",
            help="The setting for the ASGI root_path variable",
            default=getenv("ROOT_PATH", ""),
        )
        self.parser.add_argument(
            "--proxy-headers",
            dest="proxy_headers",
            help="Enable parsing and using of X-Forwarded-For and X-Forwarded-Port headers and using that as the "
            "client address",
            default=getenv("PROXY_HEADERS", False),
            action="store_true",
        )
        self.arg_proxy_host = self.parser.add_argument(
            "--proxy-headers-host",
            dest="proxy_headers_host",
            help="Specify which header will be used for getting the host "
            "part. Can be omitted, requires --proxy-headers to be specified "
            'when passed. "X-Real-IP" (when passed by your webserver) is a '
            "good candidate for this.",
            default=getenv("PROXY_HEADERS_HOST", False),
            action="store",
        )
        self.arg_proxy_port = self.parser.add_argument(
            "--proxy-headers-port",
            dest="proxy_headers_port",
            help="Specify which header will be used for getting the port "
            "part. Can be omitted, requires --proxy-headers to be specified "
            "when passed.",
            default=getenv("PROXY_HEADERS_PORT", False),
            action="store",
        )
        self.parser.add_argument(
            "application",
            help="The application to dispatch to as path.to.module:instance.path",
            default=None,
        )
        self.parser.add_argument(
            "-s",
            "--server-name",
            dest="server_name",
            help="specify which value should be passed to response header Server attribute",
            default=getenv("SERVER_NAME", "iLens/0.1"),
        )
        self.parser.add_argument(
            "--no-server-name", dest="server_name", action="store_const", const=""
        )
        self.server = None


if __name__ == "__main__":
    CommandLineInterface().entrypoint()
