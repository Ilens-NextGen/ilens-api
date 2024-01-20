import logging
import functools
from rich.logging import RichHandler
import logging.handlers

from server.utils import getlistenv, getenv, getboolenv
from server.settings import SERVER_ID as server

debug = getboolenv("DEBUG", False)
log_fmt = getenv(
    "LOG_FORMAT", f"[%(asctime)s] [{server}] [%(levelname)s] [%(name)s] %(message)s"
)
log_keywords = getlistenv("LOG_KEYWORDS", []) + [
    "INFO",
    "DEBUG",
    "WARNING",
    "ERROR",
    "CRITICAL",
    server,
]

date_fmt = getenv("LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S %z")
log_file = getenv("LOG_FILE", "ilens_server.log")
log_level = getenv("LOG_LEVEL", "DEBUG")
log_to_file = getboolenv("LOG_TO_FILE", True)


# syslog_formatter = logging.Formatter(
#     (
#         "python3.10: {"
#         ' "loggerName":"%(name)s", "timestamp":"%(asctime)s",'
#         ' "pathName":"%(pathname)s", "logRecordCreationTime":"%(created)f",'
#         ' "functionName":"%(funcName)s", "levelNo":"%(levelno)s",'
#         ' "lineNo":"%(lineno)d", "time":"%(msecs)d",'
#         ' "levelName":"%(levelname)s", "message":"%(message)s"}'
#     )
# )
# syslog_handler = logging.handlers.SysLogHandler(address="/dev/log")
# syslog_handler.setFormatter(syslog_formatter)

formatter = logging.Formatter(log_fmt, date_fmt)
stream_handler = RichHandler(
    level=log_level,
    show_time=False,
    show_path=False,
    show_level=False,
    rich_tracebacks=True,
    markup=False,
    tracebacks_show_locals=debug,
    keywords=log_keywords,
)
stream_handler.setFormatter(formatter)

logging.basicConfig(
    level=log_level,
    format=log_fmt,
    datefmt=date_fmt,
    handlers=[],
)


class CustomLogger:
    def __init__(
        self, logger_name, file_logging=log_to_file, file_name="ilens_server.log"
    ):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(log_level)  # Set the logging level
        # Prevent the log messages from being duplicated in the python.log file
        self.logger.propagate = False
        # Add the stream handler to the logger
        self.logger.addHandler(stream_handler)
        # self.logger.addHandler(syslog_handler)

        if file_logging:
            # Create a file handler
            fh = logging.FileHandler(file_name)
            # Set the logging level for the file handler
            fh.setLevel(log_level)
            # Add the formatter to the file handler
            fh.setFormatter(formatter)
            # Add the file handler to the logger
            self.logger.addHandler(fh)

    def get_logger(self):
        return self.logger

    def decorate(self, func, start_msg="Starting", end_msg="Ending", level="info"):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.logger.info
            self.logger.info(
                f"Calling {func.__name__} with args {args} and kwargs {kwargs}"
            )
            return func(*args, **kwargs)

        return wrapper


def decorate(self, func, start_msg="Starting", end_msg=None):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        self.logger.info(start_msg)
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            self.logger.error(f"{self.logger.name}Error", exc_info=True)
            raise e
        if end_msg:
            self.logger.info(end_msg)

    return wrapper
