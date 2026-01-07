from pydantic import BaseModel, Field


class ModuleStateModel(BaseModel):
    """Схема данных статуса объекта"""

    id: int = Field(description="ID статуса")
    flag: int = Field(description="Флаг")
    code: str = Field(description="Код")
    title: str = Field(description="Наименование")
    # hierarchy: str = Field(description="Иерархия")


class ModuleStateFilterCollectionModel(BaseModel):
    """Схема данных фильтрации списка статусов объектов модулей"""

    module_id: list[int] | None = Field(None, description="Список ID модулей")
