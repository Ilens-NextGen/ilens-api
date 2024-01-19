import logging
import functools
from server.utils import getlistenv, loadenv, getenv, getboolenv

loadenv()


class CustomLogger:
    def __init__(self, logger_name, file_logging=True, file_name="ilens_server.log"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)  # Set the logging level

        # Create a console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)  # Set the logging level for the console handler

        # Create a formatter
        formatter = logging.Formatter(
            "[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S %z",
        )

        # Add the formatter to the console handler
        ch.setFormatter(formatter)

        # Add the console handler to the logger
        self.logger.addHandler(ch)

        if file_logging:
            # Create a file handler
            fh = logging.FileHandler(file_name)
            fh.setLevel(logging.DEBUG)  # Set the logging level for the file handler

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
