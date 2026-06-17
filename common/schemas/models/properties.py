from pydantic import Field

from .base import AuditModel
from .modules import ModuleModel


class PropertyModel(AuditModel):
    """Схема данных свойства объекта модуля"""

    id: int = Field(description="ID записи")
    module_id: int = Field(description="ID модуля")
    name: str = Field(description="Наименование")
    is_required: bool = Field(description="Флаг обязательности")
    is_active: bool = Field(description="Флаг активности")

    module: ModuleModel = Field(description="Данные модуля")
