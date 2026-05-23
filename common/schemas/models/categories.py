from pydantic import Field

from .base import AuditModel
from .module_states import ModuleStateModel


class CategoryModel(AuditModel):
    """Схема данных категории"""

    id: int = Field(description="ID категории")
    state_id: int = Field(description="ID статуса")
    name: str = Field(description="Наименование")
    sku_prefix: str = Field(description="Префикс артикула")
    toy_max_index: int = Field(description="Максимальный индекс игрушки")

    state: ModuleStateModel = Field(description="Данные статуса категории")
