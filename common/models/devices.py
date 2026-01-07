from uuid import UUID

from sqlalchemy import String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from .base import AuditMixin, Base
from .case import DeviceCase


class Device(AuditMixin, Base):
    case = DeviceCase

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(), nullable=False)
    user_agent: Mapped[str] = mapped_column(String(), nullable=False)
