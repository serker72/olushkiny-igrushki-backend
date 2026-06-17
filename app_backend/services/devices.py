from app_backend.services.base import BaseModelService
from common.models import Device


class DeviceService(BaseModelService):
    """Сервис для работы с устройствами"""

    model_class = Device
