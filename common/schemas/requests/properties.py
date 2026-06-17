from pydantic import BaseModel, Field

from common.schemas.models import CustomBoolOrNone, CustomIntOrNone
from common.schemas.requests import BaseRetrieveCollectionRequest


class PropertyCreateRequest(BaseModel):
    """Схема запроса создания свойства объекта модуля"""

    module_id: int = Field(description="ID модуля")
    name: str = Field(description="Наименование")
    is_required: bool = Field(description="Флаг обязательности")


class PropertyUpdateRequest(PropertyCreateRequest):
    """Схема запроса изменения свойства объекта модуля"""

    is_active: bool = Field(description="Флаг активности")


class PropertyRetrieveCollectionRequest(BaseRetrieveCollectionRequest):
    """Схема запроса получения списка свойств объектов модулей"""

    limit: CustomIntOrNone = Field(default=50, description="Количество объектов на странице")
    module_id: CustomIntOrNone = Field(default=None, description="ID модуля")
    is_required: CustomBoolOrNone = Field(default=None, description="Флаг обязательности")
    is_active: CustomBoolOrNone = Field(default=None, description="Флаг активности")
