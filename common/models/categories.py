from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import AuditMixin, Base, BaseWithState
from .case import CategoryCase


class Category(AuditMixin, BaseWithState, Base):
    case = CategoryCase
    relation_fields = {"state": "state"}

    name: Mapped[str] = mapped_column(String(), nullable=False)
    sku_prefix: Mapped[str] = mapped_column(String(), nullable=False)
    toy_max_index: Mapped[int] = mapped_column(Integer(), default=0, nullable=False)
