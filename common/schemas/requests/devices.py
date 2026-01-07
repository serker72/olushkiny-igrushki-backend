from pydantic import BaseModel, Field


class DeviceCreateRequest(BaseModel):
    """Схема запроса на создание устройства"""

    device_id: str = Field(description="ID устройства")
    user_agent: str = Field(description="User Agent")
