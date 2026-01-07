from app_backend.services.base import BaseModelService
from common.models import Module


class ModuleService(BaseModelService):
    """Класс сервиса для модулей"""

    model_class = Module
    is_collection_paginate = False
