from pydantic import Field

from common.schemas.models import PropertyModel

from .base import BaseRetrieveCollectionPaginateResponse, BaseRetrieveResponse


class PropertyRetrieveResponse(BaseRetrieveResponse):
    """Схема ответа с данными свойства объекта модуля"""

    item: PropertyModel = Field(description="Данные свойства объекта модуля")


class PropertyRetrieveCollectionPaginateResponse(BaseRetrieveCollectionPaginateResponse):
    """Схема ответа со списком свойств объектов модулей с пагинацией"""

    items: list[PropertyModel] = Field(description="Список свойств объектов модулей")
