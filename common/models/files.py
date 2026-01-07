from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import AuditMixin, Base
from .case import FileCase


class File(AuditMixin, Base):
    case = FileCase
    relation_fields = {"module": "module"}

    id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False, primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"))
    entity_id: Mapped[int] = mapped_column(Integer(), nullable=True)
    entity_uuid: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=True)
    tmp_entity_uuid: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=True)
    entity_field: Mapped[str] = mapped_column(String(), nullable=False)
    entity_field_index: Mapped[int] = mapped_column(SmallInteger(), nullable=True)
    name: Mapped[str] = mapped_column(String(), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger(), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(), nullable=False)
    url: Mapped[str] = mapped_column(String(), nullable=False)
    image_width: Mapped[int] = mapped_column(SmallInteger(), nullable=True)
    image_height: Mapped[int] = mapped_column(SmallInteger(), nullable=True)

    # relations
    module = relationship("Module", viewonly=True, uselist=False, lazy="selectin")
