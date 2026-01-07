from uuid import UUID

from sqlalchemy import BigInteger, Enum, ForeignKey, SmallInteger, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.enums import UserAuthorizationCodeStatuses

from .base import AuditMixin, Base
from .case import UserAuthorizationCodeCase


class UserAuthorizationCode(AuditMixin, Base):
    case = UserAuthorizationCodeCase

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_id: Mapped[UUID] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String(), nullable=True)
    phone: Mapped[str] = mapped_column(String(), nullable=True)
    code: Mapped[str] = mapped_column(String(), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(UserAuthorizationCodeStatuses, name="user_authorization_codes_status"),
        nullable=False,
        default=UserAuthorizationCodeStatuses.created,
    )
    group_number: Mapped[int] = mapped_column(SmallInteger(), nullable=True)

    # relations
    device = relationship("Device", viewonly=True, uselist=False, lazy="selectin")
    user = relationship("User", viewonly=True, uselist=False, lazy="selectin")
