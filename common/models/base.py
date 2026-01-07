from __future__ import annotations

from asyncio import iscoroutine, iscoroutinefunction
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Type, TypeVar

# from loguru import logger
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, inspect, select
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column, relationship
from sqlalchemy.sql import ColumnExpressionArgument
from sqlalchemy.types import JSON

from common.helpers import timeutil
from common.helpers.date_time import get_dict_datetime_as_timezone
from common.helpers.string import name_singular_to_plural, to_snake_case

from .. import models
from .case import Case


@dataclass
class RelationField:
    """Класс поля связанной модели"""

    field: str
    max_recursion_level: int


class AuditMixin(AsyncAttrs):
    """Миксин для добавления полей аудита"""

    created_by: Mapped[int] = mapped_column(BigInteger(), default=1, nullable=False)
    created_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=timeutil.utcnow, nullable=False)
    updated_by: Mapped[int] = mapped_column(BigInteger(), default=1, nullable=False)
    updated_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=timeutil.utcnow, default=timeutil.utcnow, nullable=False
    )

    @declared_attr
    def creator(self):
        return relationship(
            "User",
            primaryjoin=f"foreign({self.__name__}.created_by) == remote(User.id)",
            uselist=False,
            lazy="selectin",
            post_update=True,
        )

    @declared_attr
    def updater(self):
        return relationship(
            "User",
            primaryjoin=f"foreign({self.__name__}.updated_by) == remote(User.id)",
            uselist=False,
            lazy="selectin",
            post_update=True,
        )

    @hybrid_property
    def creator_fio(self):
        return getattr(self.creator, "fio", None)

    @hybrid_property
    def updater_fio(self):
        return getattr(self.updater, "fio", None)


class Base(DeclarativeBase, AsyncAttrs):
    """Базовый класс модели"""

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)

    type_annotation_map = {dict[str, Any]: JSON}

    relation_fields: dict[str, str | RelationField] = {}
    case: Type[Case] = Case
    media_fields: list[str] = []
    multiple_media_fields: list[str] = []

    @declared_attr
    def __tablename__(self) -> str:
        """Получение имени таблицы"""
        table_name = to_snake_case(self.__name__)
        # UserSocialNetworkAccountStory => user_social_network_account_stories
        # return f"{table_name[:-1]}ies" if table_name[-1] == "y" else f"{table_name}s"
        return name_singular_to_plural(table_name)

    async def as_dict(self, level: int = -1, user_time_zone: str = None) -> dict:
        """Преобразование в словарь"""
        level += 1
        model_inspection = inspect(self)
        columns = model_inspection.mapper.column_attrs
        data = {c.key: getattr(self, c.key) for c in columns}

        # Обрабатываем гибридные свойства
        for column in model_inspection.mapper.all_orm_descriptors:
            if type(column) is hybrid_property:
                data[column.__name__] = await get_model_attr_by_key(self, column.__name__)

        # Обрабатываем словарь relation_fields - список полей связанных таблиц
        for k, v in self.relation_fields.items():
            related_field_max_recursion_level = v.max_recursion_level if isinstance(v, RelationField) else None
            related_field = await get_model_attr_by_key(self, v.field if isinstance(v, RelationField) else v)

            if isinstance(related_field, Base):
                if related_field_max_recursion_level is None or level <= related_field_max_recursion_level:
                    data[k] = await related_field.as_dict(level)
            elif isinstance(related_field, list) and len(related_field) and isinstance(related_field[0], Base):
                if related_field_max_recursion_level is None or level <= related_field_max_recursion_level:
                    data[k] = [await rf.as_dict(level) for rf in related_field]
            else:
                data[k] = related_field

        # logger.debug(f"data: {repr(data)}")
        # logger.debug(f"{self.__class__.__name__} as_dict: level={level}, data={repr(data)}")
        return get_dict_datetime_as_timezone(data, user_time_zone) if user_time_zone is not None else data

    def get_event_title(self):
        """Получение названия сущности"""
        for key in ["title", "name"]:
            if hasattr(self, key):
                return f'"{self.case.genitive.lower()} {getattr(self, key)}"'
        return f'"{self.case.genitive.lower()} ID {self.id}"'


class BaseWithPhoto(Base):
    """Класс обеспечивающий поддержку изображений"""

    __abstract__ = True

    async def photo(self):
        session = inspect(self).async_session

        state_id = getattr(self, "state_id", None)

        if state_id is None or not isinstance(state_id, (BigInteger, Integer)):
            statement = (
                select(models.File)
                .join(models.Module, models.Module.code == self.__tablename__)
                .filter(
                    models.File.entity_field == "photo",
                    models.File.entity_id == self.id,
                    models.File.module_id == models.Module.id,
                )
            )
        else:
            statement = (
                select(models.File)
                .join(models.ModuleState, models.ModuleState.id == state_id)
                .filter(
                    models.File.entity_field == "photo",
                    models.File.entity_id == self.id,
                    models.File.module_id == models.ModuleState.module_id,
                )
            )

        statement_result = await session.execute(statement)
        return statement_result.scalar()


class BaseWithPhotos(Base):
    """Класс обеспечивающий поддержку нескольких изображений"""

    __abstract__ = True

    async def photos(self):
        session = inspect(self).async_session

        state_id = getattr(self, "state_id", None)

        if state_id is None or not isinstance(state_id, (BigInteger, Integer)):
            statement = (
                select(models.File)
                .join(models.Module, models.Module.code == self.__tablename__)
                .filter(
                    models.File.entity_field == "photos",
                    models.File.entity_id == self.id,
                    models.File.module_id == models.Module.id,
                )
            )
        else:
            statement = (
                select(models.File)
                .join(models.ModuleState, models.ModuleState.id == state_id)
                .filter(
                    models.File.entity_field == "photos",
                    models.File.entity_id == self.id,
                    models.File.module_id == models.ModuleState.module_id,
                )
            )

        statement_result = await session.execute(statement)
        return statement_result.scalars().all()


class BaseWithState(Base):
    """Базовый класс модели с полем статуса объекта"""

    __abstract__ = True
    state_id: Mapped[int] = mapped_column(ForeignKey("module_states.id", ondelete="CASCADE"))

    @declared_attr
    def state(self):
        return relationship(
            "ModuleState",
            # primaryjoin=f"foreign({self.__name__}.state_id) == remote(ModuleState.id)",
            uselist=False,
            lazy="selectin",
            post_update=True,
        )


BaseType = TypeVar("BaseType", bound=Base)


@dataclass
class ModelJoinItem:
    """Класс элемента объединения таблиц"""

    target: Type[Base]
    onclause: ColumnExpressionArgument
    isouter: bool = False
    full: bool = False


async def get_model_attr_by_key(instance: Base, key: str) -> Any | None:
    """Получение атрибута экземпляра модели по указанному пути"""
    key_parts = key.split(".")
    value = await getattr(instance.awaitable_attrs, key_parts[0], None)
    if iscoroutine(value):
        value = await value
    elif iscoroutinefunction(value):
        value = await value()

    return (
        value
        if value is None or len(key_parts) == 1
        else (
            getattr(value, key_parts[1])
            if len(key_parts) == 2
            else await get_model_attr_by_key(value, ".".join(key_parts[1:]))
        )
    )
