from pydantic import BaseModel, Field

from common.schemas.models import CustomIntOrNone
from common.schemas.requests import BaseRetrieveCollectionRequest


class CategoryCreateRequest(BaseModel):
    """Схема запроса на создание категории"""

    name: str = Field(description="Наименование")
    sku_prefix: str = Field(description="Префикс артикула")


class CategoryUpdateRequest(CategoryCreateRequest):
    state_id: int = Field(description="ID статуса")


class CategoryRetrieveCollectionRequest(BaseRetrieveCollectionRequest):
    state_id: CustomIntOrNone = Field(default=None, description="ID статуса")
