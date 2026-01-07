from uuid import UUID

from pydantic import Field

from .base import AuditModel


class DeviceModel(AuditModel):
    """Схема данных устройства"""

    id: UUID = Field(description="ID записи")
    device_id: str = Field(description="ID устройства")
    user_agent: str = Field(description="User Agent")
