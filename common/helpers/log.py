import logging.handlers
import os
import sys
from os.path import join
from types import FrameType
from typing import cast

from loguru import logger

from common.helpers import constants as c
from common.helpers.file import check_directory_exists
from common.schemas.models.settings import settings


class InterceptHandler(logging.Handler):
    """Logs to loguru from Python logging module"""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        frame, depth = logging.currentframe(), 1
        while frame.f_code.co_filename in (logging.__file__, __file__):  # noqa: WPS609
            frame = cast(FrameType, frame.f_back)
            depth += 1
        logger_with_opts = logger.opt(depth=depth, exception=record.exc_info)
        try:
            logger_with_opts.log(level, "{}", record.getMessage())
        except Exception as e:
            safe_msg = getattr(record, "msg", None) or str(record)
            logger_with_opts.warning("Exception logging the following native logger message: {}, {!r}", safe_msg, e)


def module_logger_configure(module_name: str, log_level: str = "INFO") -> None:
    """Конфигурирование логгера указанного модуля"""
    mod_logger = logging.getLogger(module_name)
    mod_logger.setLevel(log_level)
    mod_logger.handlers = [InterceptHandler(level=log_level)]
    mod_logger.propagate = False


def logger_configure(application_code: str, application_id: str = None) -> None:
    """Конфигурация логгера"""
    log_level = "DEBUG" if settings.debug is True else "INFO"
    print(f"settings.debug: {settings.debug}, log_level: {log_level}")

    log_path = join(settings.backend_log_path, application_code)
    print(f"log_path: {log_path}")
    if not check_directory_exists(log_path):
        os.makedirs(log_path, exist_ok=True)

    log_file_name = f"{log_path}/{f'{application_id}.' if application_id else ''}"

    if application_code in {c.APPLICATION_CODE_BACKEND}:
        log_format = c.FORMAT_LOG_APP
        log_extra = {"app_id": "-", "request_id": "-", "user_ip": "-", "user_id": "-", "user_agent": "-"}
    elif application_code in {c.APPLICATION_CODE_QUEUE_PROCESSING}:
        log_format = c.FORMAT_LOG_QUEUE_PROCESSING
        log_extra = {"p_id": "-"}
    else:
        log_format = c.FORMAT_LOG_DEFAULT
        log_extra = None

    logger.remove()
    logger.add(sys.stderr, format=log_format, level=log_level)
    logger.add(
        log_file_name + "{time}.log",
        format=log_format,
        level=log_level,
        rotation="00:00:00",
        # compression="zip",
        retention="5 days",
    )

    if log_extra:
        logger.configure(extra=log_extra)

    if settings.sa_debug is True:
        handler = logging.handlers.SysLogHandler(address=("localhost", 514))
        logger.add(handler)

    module_logger_configure("httpx", log_level)
    module_logger_configure("aiohttp.access", log_level)
    module_logger_configure("aiohttp.client", log_level)
    module_logger_configure("aiohttp.internal", log_level)
    module_logger_configure("aiohttp.server", log_level)
    module_logger_configure("aiohttp.web", log_level)
    module_logger_configure("aiohttp.websocket", log_level)
    module_logger_configure("libre_fastapi_jwt.auth_jwt", log_level)

    return None
