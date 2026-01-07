from asyncio import current_task
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from typing import Any, Type

from alembic import op
from fastapi import Request
from loguru import logger
from sqlalchemy import and_, create_engine, event, inspect, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.sql.expression import BinaryExpression

from common.exceptions import BackendException
from common.helpers.json import custom_json_serializer
from common.models.base import Base
from common.schemas.models.settings import settings


def get_sa_engine() -> Engine:
    """Получение экземпляра подключения к БД SQLAlchemy"""
    return create_engine(
        settings.get_postgres_url(),
        json_serializer=custom_json_serializer,
        echo=settings.sa_debug,
        pool_size=settings.sa_pool_size,
        max_overflow=settings.sa_max_overflow,
        pool_timeout=settings.sa_pool_timeout,
        pool_recycle=settings.sa_pool_recycle,
        pool_use_lifo=settings.sa_pool_use_lifo,
        pool_pre_ping=settings.sa_pool_pre_ping,
    )


def get_sa_async_engine() -> AsyncEngine:
    """Получение экземпляра асинхронного подключения к БД SQLAlchemy"""
    return create_async_engine(
        settings.get_postgres_async_url(),
        json_serializer=custom_json_serializer,
        echo=settings.sa_debug,
        pool_size=settings.sa_pool_size,
        max_overflow=settings.sa_max_overflow,
        pool_timeout=settings.sa_pool_timeout,
        pool_recycle=settings.sa_pool_recycle,
        pool_use_lifo=settings.sa_pool_use_lifo,
        pool_pre_ping=settings.sa_pool_pre_ping,
    )


@event.listens_for(Session, "after_flush")
def log_flush(session, flush_context):
    """Установка флага flushed"""
    session.info["flushed"] = True
    logger.debug(f"[log_flush] session: {session} {repr(session.info)}")


@event.listens_for(Session, "after_commit")
@event.listens_for(Session, "after_rollback")
def reset_flushed(session):
    """Сброс флага flushed"""
    if "flushed" in session.info:
        del session.info["flushed"]

    logger.debug(f"[reset_flushed] session: {session} {repr(session.info)}")


def has_uncommitted_changes(session: Session):
    """Проверка необходимости выполнения commit"""
    result = (
        any(session.new)
        or any(session.deleted)
        or any([x for x in session.dirty if session.is_modified(x)])
        or session.info.get("flushed", False)
    )
    logger.debug(
        f"session: {session}, new: {any(session.new)}, deleted: {any(session.deleted)}, "
        f"is_modified: {any([x for x in session.dirty if session.is_modified(x)])}, "
        f"flushed: {session.info.get('flushed', False)}, result: {result}"
    )
    return result


def sync_sa_session_generator(sa_engine: Engine):
    """Генератор сессии SQLAlchemy"""
    return scoped_session(sessionmaker(bind=sa_engine, autocommit=False, autoflush=False))


def async_session_generator(engine: AsyncEngine):
    """Генератор асинхронной сессии SQLAlchemy"""
    async_session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
    )
    return async_scoped_session(session_factory=async_session_factory, scopefunc=current_task)


@contextmanager
def get_sa_session(sa_engine: Engine):
    """Создание сессии SQLAlchemy"""
    try:
        session_generator = sync_sa_session_generator(sa_engine)
        with session_generator() as session:
            logger.debug(f"session: {session}")
            yield session

            if has_uncommitted_changes(session):
                session.commit()
                logger.debug(f"commit session: {session}")
    except BackendException as e:
        logger.debug(f"BackendException session: {e.is_session_commit} {session}")
        if e.is_session_commit is True:
            if has_uncommitted_changes(session):
                session.commit()
                logger.debug(f"commit session: {session}")
        else:
            session.rollback()
            logger.debug(f"rollback session: {session}")

        raise
    except Exception:
        session.rollback()
        logger.debug(f"rollback session: {session}")
        raise
    finally:
        session.close()
        logger.debug(f"close session: {session}")


@asynccontextmanager
async def get_sa_async_session(engine: AsyncEngine):
    """Создание асинхронной сессии SQLAlchemy"""
    async_session = async_session_generator(engine)

    try:
        async with async_session() as session:
            logger.debug(f"session: {session}")
            yield session

            if has_uncommitted_changes(session):
                await async_session.commit()
                logger.debug(f"commit session: {session}")
    except BackendException as e:
        logger.debug(f"BackendException session: {e.is_session_commit} {session}")
        if e.is_session_commit is True:
            if has_uncommitted_changes(session):
                await async_session.commit()
                logger.debug(f"commit session: {session}")
        else:
            await async_session.rollback()
            logger.debug(f"rollback session: {session}")

        raise
    except Exception:
        await async_session.rollback()
        logger.debug(f"rollback session: {session}")
        raise
    finally:
        await async_session.remove()


def get_op_connection() -> Connection:
    """Получение подключения к БД Alembic"""
    return op.get_bind()


def get_table_records(
    con: Connection,
    table_name: str,
    key_field: str = "code",
    value_field: str = "id",
    where_keys: list[str] = None,
    data: dict = None,
    where_str: str = None,
) -> dict:
    """Получение словаря с записями таблицы"""
    sql = f"SELECT {key_field}, {value_field} FROM {table_name}"

    if where_str is not None or (where_keys is not None and data is not None):
        if where_str is None and where_keys is not None and data is not None:
            where_str = " AND ".join([f"{k} = :{k}" for k in where_keys])

        sql = f"{sql} WHERE {where_str}"

    rows = con.execute(text(sql), data).mappings().all()
    return {row[key_field]: row[value_field] for row in rows}


def get_module_actions(con: Connection) -> dict:
    """Получение словаря действий модулей."""
    sql = """
        SELECT m.code as module_code, a.code as action_code, ma.id
        FROM module_actions ma
        JOIN modules m on ma.module_id = m.id
        JOIN actions a on a.id = ma.action_id
    """
    return {
        f"{item['module_code']}.{item['action_code']}": item["id"] for item in con.execute(text(sql)).mappings().all()
    }


def add_record_to_table(
    con: Connection,
    table_name: str,
    data: dict,
    is_audit_fields: bool = True,
    user_id: int = None,
    returning_field: str = "id",
) -> Any | None:
    """Добавление записи в таблицу"""
    if is_audit_fields:
        user_id = user_id or 1
        data.update({"created_by": user_id, "updated_by": user_id})

    fields = ", ".join(data.keys())
    # values = ", ".join([f"'{v}'" if v is not None else "NULL" for v in data.values()])
    values = ", ".join([f":{k}" for k in data.keys()])

    sql = f"INSERT INTO {table_name} ({fields}) VALUES ({values})"
    if returning_field:
        sql += f" RETURNING {returning_field}"
        return con.execute(text(sql), data).scalar()

    con.execute(text(sql), data)
    return None


def add_module_actions(con: Connection, module_actions: dict = None, role_module_actions: dict = None):
    """Добавление действий модуля и прав ролям."""
    modules = get_table_records(con, "modules")
    actions = get_table_records(con, "actions")
    # Добавление действий модуля
    if isinstance(module_actions, dict) and len(module_actions):
        for module_code, items in module_actions.items():
            module_id = modules.get(module_code)
            for item_action in items:
                for action_code, title in item_action.items():
                    item = {
                        "module_id": module_id,
                        "action_id": actions.get(action_code),
                        "title": title,
                    }
                    add_record_to_table(con, "module_actions", item)

    # Добавление прав ролям
    if isinstance(role_module_actions, dict) and len(role_module_actions):
        module_actions_map = get_module_actions(con)
        roles = get_table_records(con, "roles")
        for role_code, role_items in role_module_actions.items():
            role_id = roles.get(role_code)
            for module_code, action_codes in role_items.items():
                for action_code in action_codes:
                    key = f"{module_code}.{action_code}"
                    item = {
                        "role_id": role_id,
                        "module_action_id": module_actions_map.get(key),
                    }
                    add_record_to_table(con, "role_module_actions", item)


def delete_record_from_table(
    con: Connection, table_name: str, where_keys: list[str], data: dict, returning_field: str = "id"
):
    """Удаление записи из таблицы"""
    where_str = " AND ".join([f"{k} = :{k}" for k in where_keys if data.get(k) is not None])

    where_str_null = " AND ".join([f"{k} IS NULL" for k in where_keys if data.get(k) is None])
    if where_str_null:
        where_str += " AND " + where_str_null

    sql = f"DELETE FROM {table_name} WHERE {where_str}"

    if returning_field:
        sql += f" RETURNING {returning_field}"
        return con.execute(text(sql), data).scalar()

    con.execute(text(sql), data)
    return None


def delete_module_actions(con: Connection, module_actions: dict = None, role_module_actions: dict = None):
    """Удаление действий модуля и прав ролям."""
    if isinstance(role_module_actions, dict) and len(role_module_actions):
        module_actions_map = get_module_actions(con)
        roles = get_table_records(con, "roles")
        for role_code, role_items in role_module_actions.items():
            role_id = roles.get(role_code)
            for module_code, action_codes in role_items.items():
                for action_code in action_codes:
                    key = f"{module_code}.{action_code}"
                    item = {
                        "role_id": role_id,
                        "module_action_id": module_actions_map.get(key),
                    }
                    delete_record_from_table(con, "role_module_actions", ["role_id", "module_action_id"], item)

    if isinstance(module_actions, dict) and len(module_actions):
        modules = get_table_records(con, "modules")
        actions = get_table_records(con, "actions")
        for module_code, items in module_actions.items():
            module_id = modules.get(module_code)
            for item_action in items:
                for action_code, _ in item_action.items():
                    item = {
                        "module_id": module_id,
                        "action_id": actions.get(action_code),
                    }
                    delete_record_from_table(con, "module_actions", ["module_id", "action_id"], item)


def has_hybrid_property(model: Type[Base], field: str) -> bool:
    """Проверка наличия гибридного свойства с указанным именем в указанной модели SQLAlchemy"""
    for column in inspect(model).mapper.all_orm_descriptors:
        if type(column) is hybrid_property and column.__name__ == field:
            return True

    return False


def build_datetime_range_fields_intersection_filter(
    start_date_field: datetime, finish_date_field: datetime, start_date: datetime, finish_date: datetime
) -> list[BinaryExpression]:
    """Построение условия фильтрации для проверки пересечения интервала дат с существующими интервалами"""
    return [
        and_(  # смещение вперед
            start_date_field >= start_date,
            start_date_field <= finish_date,
        ),
        and_(  # смещение назад
            finish_date_field <= finish_date,
            finish_date_field >= start_date,
        ),
        and_(  # вхождение
            start_date_field < finish_date,
            finish_date_field > start_date,
        ),
        and_(  # поглощение и совпадение
            start_date_field >= start_date,
            finish_date_field <= finish_date,
        ),
    ]


def get_request_sa_session(request: Request) -> str:
    sa_session = getattr(request.state, "sa_session", None)
    return repr(sa_session.__dict__ if sa_session else None)
