from app_backend.services.base import BaseModelService, UniqueLowerNameMixin
from common.helpers import constants as c
from common.models import Product


class ProductService(UniqueLowerNameMixin, BaseModelService):
    """Сервис для работы со свойствами"""

    model_class = Product
    entity_unique_fields = ["sku", "name"]
    entity_unique_operator = c.SA_FILTER_OPERATOR_OR
