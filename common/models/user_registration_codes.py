from uuid import UUID

from sqlalchemy import BigInteger, Enum, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.enums import UserRegistrationCodeStatuses

from .base import AuditMixin, Base
from .case import UserRegistrationCodeCase


class UserRegistrationCode(AuditMixin, Base):
    case = UserRegistrationCodeCase

    id: Mapped[int] = mapped_column(BigInteger(), nullable=False, primary_key=True)
    device_id: Mapped[UUID] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=True)
    email: Mapped[str] = mapped_column(String(), nullable=True)
    phone: Mapped[str] = mapped_column(String(), nullable=True)
    code: Mapped[str] = mapped_column(String(), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(UserRegistrationCodeStatuses, name="user_registration_codes_status"),
        nullable=False,
        default=UserRegistrationCodeStatuses.created,
    )
    group_number: Mapped[int] = mapped_column(SmallInteger(), nullable=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    # relations
    device = relationship("Device", viewonly=True, uselist=False, lazy="selectin")
    user = relationship("User", viewonly=True, uselist=False, lazy="selectin")
