from pydantic import BaseModel, Field


class ModuleModel(BaseModel):
    """Схема данных модуля объекта"""

    id: int = Field(description="ID модуля")
    code: str = Field(description="Код")
    title: str = Field(description="Наименование")
    is_used_entity_properties: bool = Field(description="Флаг использования свойств объекта")


class ModuleShortModel(BaseModel):
    """Схема данных модуля объекта"""

    id: int = Field(description="ID модуля")
    code: str = Field(description="Код")
    title: str = Field(description="Наименование")


class ModuleFilterCollectionModel(BaseModel):
    """Схема данных фильтрации списка модулей"""

    code: list[str] | None = Field(None, description="Список кодов модулей")
    is_present_in_events: bool = Field(None, description="Флаг наличия событий модуля")
