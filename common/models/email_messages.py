from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, Base
from .case import EmailMessageCase


class EmailMessage(AuditMixin, Base):
    case = EmailMessageCase

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    user_email: Mapped[str] = mapped_column(String(), nullable=False)
    event_code: Mapped[str] = mapped_column(String(), nullable=False)
    subject: Mapped[str] = mapped_column(String(), nullable=False)
    body: Mapped[str] = mapped_column(String(), nullable=False)
    # description: Mapped[str] = mapped_column(String(), nullable=True)
    is_sent: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    is_error: Mapped[bool] = mapped_column(Boolean(), nullable=True)
    sending_errors: Mapped[postgresql.JSONB] = mapped_column(postgresql.JSONB(), nullable=True)
    repeated_attempts: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)

    # relations
    user = relationship(
        "User",
        viewonly=True,
        uselist=False,
        lazy="selectin",
        backref="email_messages",
    )
