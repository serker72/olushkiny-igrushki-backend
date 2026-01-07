from pydantic import BaseModel, Field

from common.schemas.models import ModuleModel


class ModuleRetrieveCollectionResponse(BaseModel):
    """Схема ответа со списком модулей"""

    items: list[ModuleModel] = Field(description="Список модулей")


class ModuleRetrieveResponse(BaseModel):
    """Схема базового ответа с данными модуля"""

    item: ModuleModel = Field(description="Данные модуля")
