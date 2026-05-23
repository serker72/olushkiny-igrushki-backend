from pydantic import Field

from common.schemas.models import CategoryModel

from .base import BaseRetrieveCollectionPaginateResponse, BaseRetrieveResponse


class CategoryRetrieveResponse(BaseRetrieveResponse):
    """Схема ответа с данными категории"""

    item: CategoryModel = Field(description="Данные категории")


class CategoryRetrieveCollectionPaginateResponse(BaseRetrieveCollectionPaginateResponse):
    """Схема ответа со списком категорий с пагинацией"""

    items: list[CategoryModel] = Field(description="Список категорий")
