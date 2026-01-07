from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship
from sqlalchemy_utils import LtreeType

from .base import AuditMixin, Base
from .case import ModuleStateCase


class ModuleState(AuditMixin, Base):
    case = ModuleStateCase

    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"))
    flag: Mapped[int] = mapped_column(Integer(), nullable=False)
    code: Mapped[str] = mapped_column(String(), nullable=False)
    title: Mapped[str] = mapped_column(String(), nullable=False)
    hierarchy: Mapped[str] = mapped_column(LtreeType(), nullable=True)

    # relations
    module = relationship(
        "Module",
        viewonly=True,
        uselist=False,
        lazy="selectin",
        backref=backref("states", uselist=True, lazy="selectin"),
    )
