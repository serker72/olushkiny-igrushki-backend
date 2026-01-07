from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, Base
from .case import UserDeviceCase


class UserDevice(AuditMixin, Base):
    case = UserDeviceCase

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False, primary_key=True)
    device_id: Mapped[UUID] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    last_logged_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # relations
    device = relationship("Device", viewonly=True, uselist=False, lazy="selectin")
    user = relationship("User", viewonly=True, uselist=False, lazy="selectin")
