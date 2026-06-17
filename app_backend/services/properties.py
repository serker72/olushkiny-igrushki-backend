from app_backend.services.base import BaseModelService, UniqueLowerNameMixin
from common.models import Property


class PropertyService(UniqueLowerNameMixin, BaseModelService):
    """Сервис для работы со свойствами"""

    model_class = Property
    entity_unique_fields = ["module_id", "name"]
