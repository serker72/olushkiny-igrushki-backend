from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, Base
from .case import PropertyCase


class Property(AuditMixin, Base):
    case = PropertyCase
    relation_fields = {"module": "module"}

    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), default=True, nullable=False)

    # relations
    module = relationship("Module", viewonly=True, uselist=False, lazy="selectin")
