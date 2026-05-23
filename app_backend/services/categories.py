from sqlalchemy import Column, func
from sqlalchemy.sql.expression import BinaryExpression

from app_backend.services.base import BaseModelService
from common.models import Category


class CategoryService(BaseModelService):
    """Сервис для работы с категориями"""

    model_class = Category

    is_create_event_registration = False
    is_update_event_registration = False
    is_change_state_event_registration = False
    is_delete_event_registration = False
    entity_unique_fields = ["name", "sku_prefix"]

    async def entity_check_unique_name(self, attr: Column, value: str) -> BinaryExpression:
        """Проверка уникальности объекта по полю `name`"""
        return func.lower(attr) == value.lower()
