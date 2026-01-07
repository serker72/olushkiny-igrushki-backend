from app_backend.services.base import BaseModelService
from common.models import UserDevice


class UserDeviceService(BaseModelService):
    """Сервис для работы с привязкой пользователей и устройств"""

    model_class = UserDevice

    is_create_event_registration = False
    is_update_event_registration = False
    is_change_state_event_registration = False
    is_delete_event_registration = False
