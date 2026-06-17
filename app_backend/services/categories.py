from app_backend.services.base import BaseModelService, UniqueLowerNameMixin
from common.models import Category


class CategoryService(UniqueLowerNameMixin, BaseModelService):
    """Сервис для работы с категориями"""

    model_class = Category
    entity_unique_fields = ["name", "sku_prefix"]
