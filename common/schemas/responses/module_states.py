from pydantic import BaseModel, Field

from common.schemas.models import ModuleStateModel


class ModuleStateRetrieveCollectionResponse(BaseModel):
    """Схема ответа со списком статусов объектов модулей"""

    items: dict[str, list[ModuleStateModel]] = Field(description="Список статусов объектов модулей")
