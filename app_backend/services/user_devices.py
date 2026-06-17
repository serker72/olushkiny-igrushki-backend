from app_backend.services.base import BaseModelService
from common.models import UserDevice


class UserDeviceService(BaseModelService):
    """Сервис для работы с привязкой пользователей и устройств"""

    model_class = UserDevice
