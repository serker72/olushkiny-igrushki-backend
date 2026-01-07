from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import AuditMixin, Base
from .case import ModuleCase


class Module(AuditMixin, Base):
    case = ModuleCase
    relation_fields = {"states": "states"}

    code: Mapped[str] = mapped_column(String(), nullable=False)
    title: Mapped[str] = mapped_column(String(), nullable=False)
    # label: Mapped[str] = mapped_column(String(), nullable=True)
