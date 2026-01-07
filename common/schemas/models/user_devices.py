from datetime import datetime
from uuid import UUID

from pydantic import Field

from .base import AuditModel


class UserDeviceModel(AuditModel):
    """Схема данных связи пользователя и устройства"""

    id: UUID = Field(description="ID записи")
    user_id: int = Field(description="ID пользователя")
    device_id: UUID = Field(description="ID устройства")
    last_logged_on: datetime | None = Field(default=None, description="Дата последней авторизации")
