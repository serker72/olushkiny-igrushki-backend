from decimal import Decimal

from sqlalchemy import DECIMAL, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, Base
from .case import ProductPropertyCase


class ProductProperty(AuditMixin, Base):
    case = ProductPropertyCase
    relation_fields = {
        "product": "product",
        "property": "property",
    }

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"))
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(16, 2), nullable=False)
    price: Mapped[Decimal] = mapped_column(DECIMAL(16, 2), nullable=False)
    cost: Mapped[Decimal] = mapped_column(DECIMAL(16, 2), nullable=False)

    # relations
    product = relationship("Product", viewonly=True, uselist=False, lazy="selectin")
    property = relationship("Property", viewonly=True, uselist=False, lazy="selectin")
