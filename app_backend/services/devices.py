from app_backend.services.base import BaseModelService
from common.models import Device


class DeviceService(BaseModelService):
    """Сервис для работы с устройствами"""

    model_class = Device

    is_create_event_registration = False
    is_update_event_registration = False
    is_change_state_event_registration = False
    is_delete_event_registration = False
