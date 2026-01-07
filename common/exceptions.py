from os import getcwd, scandir, sep
from os.path import join
from string import Template

from fastapi import status
from loguru import logger
from pydantic import BaseModel, Field
from pydantic_i18n import JsonLoader, PydanticI18n

from common.helpers import constants as c
from common.helpers.dict import get_dict_items

"""
Загрузка файлов с переводами сообщений приложения и библиотек:
- файлы с переводами сообщений приложения располагаются в каталоге `translations/app`
- файлы с переводами сообщений библиотеки располагаются в каталоге `translations/{library-name}`
"""
translation_folders = [f.path for f in scandir(join(getcwd(), "translations")) if f.is_dir()]
translation_loaders = {folder.split(sep)[-1]: JsonLoader(folder) for folder in translation_folders}
pydantic_error_translator = PydanticI18n(translation_loaders.get("pydantic"))


class BackendExceptionContentModel(BaseModel):
    """Схема ответа с ошибкой"""

    status_code: int = Field(description="Код статуса")
    code: str = Field(description="Код ошибки")
    message: str = Field(description="Сообщение об ошибке")
    data: dict = Field(description="Данные ошибки")


class BackendExceptionContentWithTracebackModel(BackendExceptionContentModel):
    """Схема ответа с ошибкой и трассировкой"""

    traceback: str = Field(description="Трассировка ошибки")


class BackendException(Exception):
    """
    Базовый класс ошибки.

    Attributes:
        translation_loader_key (str): ключ загрузчика шаблона сообщения, по умолчанию `app`
        locale (str): код локали
        status_code (int): код статуса HTTP, по умолчанию `400`
        is_session_commit (bool): флаг необходимости выполнения commit в сессии SQLAlchemy, по умолчанию `False`
        nested_message_context_key (str): ключ переменной для подстановки вложенного шаблона в шаблон сообщения, по умолчанию `error`
        code (str): код шаблона сообщения
        message_context (dict): словарь переменных и их значений для подстановки в шаблон сообщения
        context (dict): словарь дополнительных данных
        traceback (str): стек ошибки
        nested_code (str): код вложенного шаблона сообщения
        nested_translation_loader_key (str): ключ загрузчика вложенного шаблона сообщения
    """

    translation_loader_key: str = "app"
    locale: str = c.LOCALE_DEFAULT
    status_code: int = status.HTTP_400_BAD_REQUEST
    is_session_commit: bool = False
    nested_message_context_key: str = "error"
    code: str = None
    message_context: dict = None
    context: dict = None
    traceback: str = None
    nested_code: str = None
    nested_translation_loader_key: str = None

    def __init__(self, **kwargs):
        """Конструктор класса"""
        self.__dict__.update(kwargs)

        if not isinstance(self.message_context, dict):
            self.message_context = {}

        if not isinstance(self.context, dict):
            self.context = {}

        if self.translation_loader_key not in translation_loaders.keys():
            raise ValueError(f"Translation key {self.translation_loader_key} not found in translation_loaders")

        if self.nested_translation_loader_key and self.nested_translation_loader_key not in translation_loaders.keys():
            raise ValueError(f"Translation key {self.nested_translation_loader_key} not found in translation_loaders")

    def get_message(self) -> str:
        """Получение текста сообщения об ошибке"""
        if nested_translation := (
            self.nested_translation_loader_key
            and self.nested_translation_loader_key
            and self.nested_message_context_key
            and translation_loaders.get(self.nested_translation_loader_key)
        ):
            nested_message = nested_translation.gettext(self.nested_code, self.locale)
            logger.debug(f"nested_message: {nested_message}")
            if nested_message != self.nested_code:
                self.message_context[self.nested_message_context_key] = nested_message
                logger.debug(f"self.message_context: {repr(self.message_context)}")

        translation = translation_loaders.get(self.translation_loader_key)
        logger.debug(f"translation: {repr(translation)}")
        logger.debug(f"self.code: {self.code}")
        logger.debug(f"self.locale: {self.locale}")
        message = translation.gettext(self.code, self.locale)
        logger.debug(f"message: {message}")
        if message == self.code:
            message = translation.gettext("exception_code_not_found", self.locale)
            return Template(message).safe_substitute({"code": self.code})

        return Template(message).safe_substitute(self.message_context)

    def get_content(self) -> BackendExceptionContentModel | BackendExceptionContentWithTracebackModel:
        """Получение данных исключения"""
        params = {
            "status_code": self.status_code,
            "code": self.code,
            "message": self.get_message(),
            "data": self.context,
        }
        if self.traceback is not None:
            params["traceback"] = self.traceback

        return (
            BackendExceptionContentWithTracebackModel(**params)
            if self.traceback is not None
            else BackendExceptionContentModel(**params)
        )


class UnauthorizedException(BackendException):
    status_code = status.HTTP_401_UNAUTHORIZED


class ForbiddenException(BackendException):
    status_code: int = status.HTTP_403_FORBIDDEN


class NotFoundException(BackendException):
    status_code: int = status.HTTP_404_NOT_FOUND


class MethodNotAllowedException(BackendException):
    status_code: int = status.HTTP_405_METHOD_NOT_ALLOWED


class ConflictException(BackendException):
    status_code: int = status.HTTP_409_CONFLICT


class UnprocessableEntityException(BackendException):
    status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY


class ServerErrorException(BackendException):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR


class BadGatewayException(BackendException):
    status_code: int = status.HTTP_502_BAD_GATEWAY


class ServiceUnavailableException(BackendException):
    status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE


def get_responses(status_codes: list[int] = None) -> dict[int, dict]:
    """Получение словаря ответов на запросы"""
    responses = {
        status.HTTP_200_OK: {"description": "Успешная обработка запроса"},
        status.HTTP_204_NO_CONTENT: {"description": "Успешная обработка запроса, ответ не предполагается"},
        status.HTTP_400_BAD_REQUEST: {
            "model": BackendExceptionContentModel,
            "description": "Неизвестная ошибка при обработке запроса",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": BackendExceptionContentModel,
            "description": "Не авторизован",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": BackendExceptionContentModel,
            "description": "Нет доступа",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": BackendExceptionContentModel,
            "description": "Объект не обнаружен",
        },
        status.HTTP_409_CONFLICT: {
            "model": BackendExceptionContentModel,
            "description": "Ошибка при обработке запроса",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": BackendExceptionContentModel,
            "description": "Ошибка валидации параметров запроса",
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": BackendExceptionContentModel,
            "description": "Слишком много запросов",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": BackendExceptionContentModel,
            "description": "Внутренняя ошибка при обработке запроса",
        },
    }

    status_codes = status_codes or []
    status_codes = list(
        set(
            status_codes
            + [
                status.HTTP_200_OK,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                # status.HTTP_500_INTERNAL_SERVER_ERROR,
            ]
        )
    )
    sorted(status_codes)
    return get_dict_items(responses, status_codes)
