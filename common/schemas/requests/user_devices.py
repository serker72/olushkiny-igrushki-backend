from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserDeviceCreateRequest(BaseModel):
    """Схема запроса на создание связи пользователя, устройства и токена"""

    user_id: int = Field(description="ID пользователя")
    device_id: UUID = Field(description="ID устройства")
    last_logged_on: datetime | None = Field(default=None, description="Время последней авторизации")
