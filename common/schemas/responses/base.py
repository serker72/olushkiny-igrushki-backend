import json
from typing import Any

from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from common.exceptions import BackendExceptionContentModel, BackendExceptionContentWithTracebackModel
from common.helpers.json import CustomJsonEncoder


class CustomJSONResponse(JSONResponse):
    """Класс ответа в формате JSON"""

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(",", ":"),
            cls=CustomJsonEncoder,
        ).encode("utf-8")


class SuccessResponse(BaseModel):
    """Схема ответа с данными успешной обработки события"""

    status: str = Field(default="success", description="Статус обработки события")
    data: dict | None = Field(description="Результат обработки события")


class ErrorResponse(BaseModel):
    """Схема ответа с данными ошибки при обработке события"""

    status: str = Field(default="error", description="Статус обработки события")
    error: BackendExceptionContentModel | BackendExceptionContentWithTracebackModel = Field(
        description="Данные ошибки, возникшей при обработке события"
    )


class BaseModelResponse(BaseModel):
    """Схема базового ответа для объекта модели"""

    model_config = ConfigDict(extra="allow")


class BaseRetrieveResponse(BaseModel):
    """Схема базового ответа с данными объекта"""

    item: BaseModelResponse


class BaseRetrieveCollectionResponse(BaseModel):
    """Схема базового ответа со списком объектов"""

    items: list[BaseModelResponse] = Field(description="Список объектов")


class BaseRetrieveCollectionPaginateResponse(BaseModel):
    """Схема базового ответа со списком объектов с пагинацией"""

    items: list[BaseModelResponse] = Field(description="Список объектов")
    limit: int = Field(description="Количество записей на странице")
    page: int = Field(description="Номер страницы")
    pages: int = Field(description="Количество страниц")
    total: int = Field(description="Количество записей")


class BaseFileDownloadResponse(BaseModel):
    """Схема ответа с данными файла"""

    name: str = Field(description="Имя файла")
    size: int = Field(description="Размер файла")
    mime_type: str | None = Field(None, description="MIME-тип файла")
    content: bytes = Field(description="Содержимое файла")
