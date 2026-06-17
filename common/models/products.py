from datetime import date
from decimal import Decimal

from sqlalchemy import DECIMAL, Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, Base, BaseWithState
from .case import ProductCase


class Product(AuditMixin, BaseWithState, Base):
    case = ProductCase
    relation_fields = {"state": "state"}

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    sku: Mapped[str] = mapped_column(String(), nullable=False)
    name: Mapped[str] = mapped_column(String(), nullable=False)
    is_permanent_toys: Mapped[bool] = mapped_column(Boolean(), default=True, nullable=False)
    creation_date: Mapped[date] = mapped_column(Date(), nullable=False)
    author: Mapped[str] = mapped_column(String(), nullable=True)
    size: Mapped[Decimal] = mapped_column(DECIMAL(16, 2), nullable=False)
    cost_of_work: Mapped[Decimal] = mapped_column(DECIMAL(16, 2), nullable=False)
    cost_of_materials: Mapped[Decimal] = mapped_column(DECIMAL(16, 2), nullable=False)
    price: Mapped[Decimal] = mapped_column(DECIMAL(16, 2), nullable=False)
    price_for_sale: Mapped[Decimal] = mapped_column(DECIMAL(16, 2), nullable=False)
    profit: Mapped[Decimal] = mapped_column(DECIMAL(16, 2), nullable=False)
    hook_number: Mapped[str] = mapped_column(Integer(), nullable=True)
    spoke_number: Mapped[str] = mapped_column(Integer(), nullable=True)

    # relations
    category = relationship("Category", viewonly=True, uselist=False, lazy="selectin")
