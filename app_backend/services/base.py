from __future__ import annotations

import importlib.util
from collections import Counter, defaultdict
from inspect import stack
from typing import Any, Callable, Sequence, Type, TypeVar
from uuid import UUID, uuid4

from fastapi.templating import Jinja2Templates
from jinja2.exceptions import TemplateNotFound
from libre_fastapi_jwt import AuthJWT
from loguru import logger
from psycopg2.errorcodes import FOREIGN_KEY_VIOLATION
from pydantic import BaseModel
from sqlalchemy import (
    BigInteger,
    Column,
    Integer,
    Select,
    asc,
    delete,
    desc,
    func,
    label,
    or_,
    select,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, Session
from sqlalchemy.schema import Sequence as SASequence
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy_utils import Ltree

from common.exceptions import (
    BackendException,
    ConflictException,
    ForbiddenException,
    MethodNotAllowedException,
    NotFoundException,
    ServerErrorException,
    UnprocessableEntityException,
)
from common.helpers import constants as c
from common.helpers.classes import (
    ACSCheckActionType,
    ACSCheckActionTypes,
    BaseObject,
    set_instance_attribute_values,
)
from common.helpers.exception import get_traceback
from common.helpers.function import execute_function, execute_function_default
from common.helpers.rabbitmq import async_publish_message
from common.helpers.string import name_plural_to_singular, to_camel_case
from common.models import Base, BaseType, EmailMessage, ModelJoinItem, ModuleState, User
from common.schemas.models import BackendSettings, BaseModelType, ImageParamSchema
from common.schemas.requests import (
    BaseChangeStateRequest,
    BaseDeleteRequest,
    BaseRetrieveCollectionRequest,
)


class ServiceManager(BaseObject):
    """Класс менеджера сервисов"""

    settings: BackendSettings = None
    templates: Jinja2Templates = None
    jwt_auth: AuthJWT = None

    @staticmethod
    def get_service_class_name(module_code: str) -> str:
        """Получение имени класса сервиса для указанного модуля"""
        return "".join(to_camel_case(name_plural_to_singular(module_code), True) + ["Service"])

    def get_service(
        self,
        module_code: str,
        request_id: str,
        session: AsyncSession | Session,
        user_id: int = None,
        user_role: dict = None,
        user_time_zone: str = None,
        user_agent: str = None,
        view_action: str = None,
    ) -> BaseServiceType:
        """Получение экземпляра класса сервиса для указанного модуля"""
        expected_class = self.get_service_class_name(module_code)
        service_class = next(
            (
                cls
                for cls in (BaseService.__subclasses__() + BaseModelService.__subclasses__())
                if cls.__name__ == expected_class
            ),
            None,
        )
        logger.debug(f"expected_class={expected_class}, service_class={repr(service_class)}")

        if service_class is None:
            raise MethodNotAllowedException(
                code="class_not_implemented", message_context={"class_name": expected_class}
            )

        instance = service_class(
            request_id=request_id,
            session=session,
            user_id=user_id,
            user_role=user_role,
            user_agent=user_agent,
            user_time_zone=user_time_zone,
            settings=self.settings,
            jwt_auth=self.jwt_auth,
            templates=self.templates,
            service_manager=self,
        )

        return instance


class BaseService(BaseObject):
    """Базовый класс сервиса"""

    app_code: str = c.APPLICATION_CODE_BACKEND
    service_manager: ServiceManager = None
    request_id: str = None
    session: AsyncSession | Session = None
    settings: BackendSettings = None
    templates: Jinja2Templates = None
    jwt_auth: AuthJWT = None
    user_id: int = None
    user_role: dict = None
    user_time_zone: str = None
    user_agent: str = None

    def get_service(self, module_code: str | InstrumentedAttribute) -> BaseServiceType:
        """Получение экземпляра сервиса для указанного модуля"""
        return self.service_manager.get_service(
            module_code=module_code,
            request_id=self.request_id,
            session=self.session,
            user_id=self.user_id,
            user_role=self.user_role,
            user_agent=self.user_agent,
        )

    async def flush_and_refresh_entity(self, entity: Base = None):
        """Сохранение объекта указанного класса модели"""
        await self.session.flush()
        if entity is not None:
            await self.session.refresh(entity)

    async def commit_and_refresh_entity(self, entity: Base = None):
        """Сохранение объекта указанного класса модели"""
        await self.session.commit()
        if entity is not None:
            await self.session.refresh(entity)

    async def get_entity(
        self,
        entity_model: Type[Base],
        field_value: Any,
        field_name: str = "id",
        field_title: str = "ID",
        exception_code: str = "entity_not_found",
        is_raise_exception: bool = True,
        exception_class: Type[BackendException] = NotFoundException,
    ) -> BaseType | None:
        """Получение объекта указанного класса модели по ID"""
        filters = [getattr(entity_model, field_name) == field_value]
        entity = await self.get_entity_by_filters(
            entity_model=entity_model,
            filters=filters,
            exception_code=exception_code,
            is_raise_exception=False,
            exception_class=exception_class,
        )

        if entity is None and is_raise_exception is True:
            raise exception_class(
                code=exception_code,
                message_context={
                    "title": entity_model.case.nominative,
                    "field_title": field_title,
                    "field_value": field_value,
                },
            )

        return entity

    async def get_entity_by_filters(
        self,
        entity_model: Type[Base],
        filters: list[BinaryExpression],
        exception_code: str = "entity_not_found",
        is_raise_exception: bool = True,
        orders: list = None,
        exception_class: Type[BackendException] = NotFoundException,
    ) -> BaseType | None:
        """Получение объекта указанного класса модели по списку фильтров"""
        statement = select(entity_model).where(*filters)
        if orders is not None:
            statement = statement.order_by(*orders)
        statement_result = await self.session.execute(statement)
        entity = statement_result.scalar()

        if entity is None and is_raise_exception is True:
            raise exception_class(code=exception_code, message_context={"title": entity_model.case.nominative})

        return entity

    async def get_entities(
        self, entity_model: Type[Base], filters: list[BinaryExpression] = None
    ) -> Sequence[BaseType]:
        """Получение списка объектов указанного класса модели по списку фильтров"""
        filters = filters or []
        statement = select(entity_model)

        if len(filters) > 0:
            statement = statement.where(*filters)

        statement_result = await self.session.execute(statement)
        return statement_result.scalars().all()

    async def get_existing_entity_ids(
        self, entity_model: Type[Base], entity_ids: list[int], model_field: str = "id"
    ) -> Sequence[int]:
        """Получение списка идентификаторов существующих объектов по списку идентификаторов"""
        field = getattr(entity_model, model_field)
        statement = select(field).where(field.in_(entity_ids))
        statement_result = await self.session.execute(statement)
        return statement_result.scalars().all()

    async def validate_entity_related_object_ids(
        self,
        object_ids: list[int],
        object_entity_title: str,
        object_model: Type[Base] = None,
        existing_object_ids: list[int] = None,
        is_required: bool = False,
        maximum_allowed_number: int = None,
    ):
        """Валидация списка идентификаторов связанных объектов"""
        if not len(object_ids):
            if is_required is True:
                raise UnprocessableEntityException(
                    code="entity_related_object_ids_empty",
                    message_context={"title": object_entity_title},
                )

            return

        ids = list(set(object_ids))
        if len(ids) != len(object_ids):
            counters = Counter(object_ids)
            duplicate_ids = [item for item, count in counters.items() if count > 1]
            raise UnprocessableEntityException(
                code="entity_related_object_ids_duplicate",
                context={"items": duplicate_ids},
                message_context={"title": object_entity_title},
            )

        existing_object_ids = existing_object_ids or await self.get_existing_entity_ids(object_model, object_ids)

        ids = set(object_ids) - set(existing_object_ids)
        if len(ids):
            raise UnprocessableEntityException(
                code="entity_related_object_ids_missing",
                context={"items": ids},
                message_context={"title": object_entity_title},
            )

        if maximum_allowed_number and len(object_ids) > maximum_allowed_number:
            raise UnprocessableEntityException(
                code="entity_related_object_ids_maximum_allowed_number_has_been_exceeded",
                message_context={"title": object_entity_title, "count": maximum_allowed_number},
            )

    async def get_sequence_next_value(self, sequence_name: str):
        """Получение следующего значения генератора последовательности"""
        return await self.session.execute(SASequence(sequence_name))

    def set_template_context_common_params(self, context: dict):
        """Добавление общих параметров в контекст шаблона"""
        if "client_url" not in context.keys():
            context["client_url"] = self.settings.backend_base_url

        if "system_name" not in context.keys():
            context["system_name"] = self.settings.backend_system_name

        if "server_name" not in context.keys():
            context["server_name"] = self.settings.backend_server_name

    def render_template(self, template_name: str, context: dict) -> str:
        """Рендеринг шаблона"""
        try:
            template = self.templates.get_template(template_name)
        except TemplateNotFound as e:
            trace = get_traceback(e)
            logger.error(trace)
            raise ServerErrorException(code="template_file_not_found", message_context={"name": template_name})

        self.set_template_context_common_params(context)

        return template.render(context)

    async def send_email(
        self, event_code: str, user_id: int | None, user_email: str, entity: Base | BaseModel | dict
    ) -> dict:
        """Отправка электронного сообщения пользователю"""
        context = (
            entity.copy()
            if isinstance(entity, dict)
            else {"entity": await entity.as_dict() if isinstance(entity, Base) else entity.model_dump()}
        )

        message = EmailMessage(
            id=uuid4(),
            user_id=user_id,
            user_email=user_email,
            event_code=event_code,
            subject=self.render_template(f"email/{event_code}_subject.jinja2", context),
            body=self.render_template(f"email/{event_code}_body.jinja2", context),
            # description=context.get("description"),
        )
        self.session.add(message)
        await self.flush_and_refresh_entity(message)

        # Отправка события в очередь RabbitMQ
        queue_key = c.RABBITMQ_QUEUE_EMAIL_MESSAGES

        await async_publish_message(
            app_id=self.app_code,
            queue_name=self.settings.queue_processing_queues[queue_key].queue_name,
            data=await message.as_dict(),
            delay_time=self.settings.queue_processing_queues[queue_key].message_delay_time * 1000,
            message_id=message.id,
        )

        return {"message_id": message.id, "subject": message.subject}

    # async def get_role_module_actions(self, entity_id: int) -> dict:
    #     """Получение списка доступных действий модулей"""
    #     statement = (
    #         select(
    #             Module.code.label("module_code"),
    #             label("action_codes", func.json_agg(postgresql.aggregate_order_by(Action.code, Action.code.asc()))),
    #         )
    #         .select_from(RoleModuleAction)
    #         .join(ModuleAction, ModuleAction.id == RoleModuleAction.module_action_id)
    #         .join(Module, Module.id == ModuleAction.module_id)
    #         .join(Action, Action.id == ModuleAction.action_id)
    #         .where(RoleModuleAction.role_id == entity_id)
    #         .group_by(Module.code)
    #         .order_by(Module.code)
    #     )
    #     statement_result = await self.session.execute(statement)
    #     return {row.module_code: row.action_codes for row in statement_result.all()}


class BaseModelService(BaseService):
    """Базовый класс сервиса для операций CRUD"""

    model_class: Type[Base] = None
    entity_schemas: dict[str, BaseModel] = None
    schemas: dict[str, BaseModel] = None
    view_action: str = None

    entity_create_additional_fields: dict = {}
    entity_update_additional_fields: dict = {}
    entity_unique_fields: list[str | list[str]] = None
    entity_unique_operator: str = c.SA_FILTER_OPERATOR_AND
    entity_unique_exclude_states: list[str] = [c.STATE_DELETED]
    new_entity_state_code: str = c.STATE_DRAFT
    change_state_transitions: dict = None
    change_state_actions: dict[str, ACSCheckActionType] = None

    is_collection_paginate: bool = True
    is_ignore_similar_state: bool = False
    is_create_event_registration: bool = True
    is_update_event_registration: bool = True
    is_change_state_event_registration: bool = True
    is_delete_event_registration: bool = True
    is_physical_delete: bool = False

    # _module_states: dict[str, ModuleState] = None
    # _other_module_states: dict[str, dict[str, ModuleState]] = None

    @staticmethod
    def check_user_is_entity_owner(entity: Base, user_id: int) -> bool:
        """Проверка принадлежности объекта пользователю"""
        owner_field = "id" if entity is User else "user_id"
        return getattr(entity, owner_field, None) == user_id

    @staticmethod
    def get_model_class(module_code: str) -> Type[Base]:
        """Получение класса модели объекта по коду модуля"""
        # model_class_name = to_camel_case(f"{module_code[:-3]}y" if module_code.endswith("ies") else module_code[:-1])
        # models = importlib.import_module(f"common.models")
        # model_class = getattr(models, model_class_name, None)
        expected_class = to_camel_case(name_plural_to_singular(module_code))
        model_class = next((cls for cls in Base.__subclasses__() if cls.__name__ == expected_class), None)
        logger.debug(f"expected_class={expected_class}, model_class={repr(model_class)}")
        if model_class is None:
            raise MethodNotAllowedException(
                code="class_not_implemented", message_context={"class_name": expected_class}
            )

        return model_class

    def get_model_module_code(self, model_class: Type[Base] = None) -> str:
        """Получение кода модуля"""
        model_class = model_class or self.model_class
        return str(model_class.__tablename__)

    async def get_module_states(self, module_code: str = None) -> dict[str, ModuleState]:
        """Получение списка статусов объекта указанного модуля"""
        module_code = module_code or self.get_model_module_code(self.model_class)
        statement = select(ModuleState).where(ModuleState.hierarchy.descendant_of(Ltree(module_code)))
        statement_result = await self.session.execute(statement)
        return {state.code: state for state in statement_result.scalars().all()}

    async def get_module_state_ids(
        self, module_code: str = None, include_state_codes: list[str] = None, exclude_state_codes: list[str] = None
    ) -> Sequence[int]:
        """Получение списка идентификаторов указанных статусов объекта указанного модуля"""
        module_code = module_code or self.get_model_module_code(self.model_class)

        filters = [ModuleState.hierarchy.descendant_of(Ltree(module_code))]

        if isinstance(include_state_codes, list) and len(include_state_codes) > 0:
            filters.append(ModuleState.code.in_(include_state_codes))

        if isinstance(exclude_state_codes, list) and len(exclude_state_codes) > 0:
            filters.append(ModuleState.code.notin_(exclude_state_codes))

        statement = select(ModuleState.id).where(*filters)
        statement_result = await self.session.execute(statement)
        return statement_result.scalars().all()

    async def get_entity_for_delete(self, entity_id: int) -> Base:
        """Получение объекта для удаления"""
        return await self.get_entity(self.model_class, entity_id)

    async def get_entity_for_update(self, entity_id: int) -> Base:
        """Получение объекта для обновления"""
        return await self.get_entity(self.model_class, entity_id)

    async def entity_to_schema(
        self,
        entity: Base,
        model_class: Type[Base] = None,
        schema_class: Type[BaseModel] = None,
        action: str = None,
        image_params: ImageParamSchema = None,
    ) -> BaseModelType:
        """Получение экземпляра схемы данных для экземпляра модели"""
        model_class = model_class or self.model_class
        if (
            schema_class is None
            and action is not None
            and isinstance(self.entity_schemas, dict)
            and action in self.entity_schemas.keys()
        ):
            schema_class = self.entity_schemas.get(action).__name__
        else:
            schema_class = (schema_class and schema_class.__name__) or f"{model_class.__name__}Model"

        schemas = importlib.import_module("common.schemas.models")
        schema = getattr(schemas, schema_class, None)
        if schema is None:
            raise MethodNotAllowedException(code="class_not_implemented", message_context={"class_name": schema_class})

        entity_dict = await entity.as_dict(user_time_zone=self.user_time_zone)

        if hasattr(schema, "view_action"):
            schema.view_action = action

        if hasattr(schema, "image_params"):
            schema.image_params = image_params

        return schema(**entity_dict)

    def result_to_schema(
        self, action: str, result: dict, model_class: Type[Base] = None, schema_class: Type[BaseModel] = None
    ) -> BaseModel:
        """Получение экземпляра схемы данных для ответа"""
        model_class = model_class or self.model_class

        if schema_class is None:
            if isinstance(self.schemas, dict) and len(self.schemas) and action and self.schemas.get(action):
                schema_class = self.schemas[action].__name__
            else:
                model_name = model_class.__name__
                action_name = to_camel_case(action)
                schema_class = f"{model_name}{action_name}Response"
        else:
            schema_class = schema_class.__name__

        logger.debug(f"schema_class: {schema_class}")
        schemas = importlib.import_module("common.schemas.responses")
        schema = getattr(schemas, schema_class, None)
        if schema is None:
            raise MethodNotAllowedException(code="class_not_implemented", message_context={"class_name": schema_class})

        return schema(**result)

    def retrieve_query(self, entity_id: int | UUID) -> Select:
        """Построение запроса получения объекта"""
        return select(self.model_class).where(self.model_class.id == entity_id)

    def retrieve_model_class(self) -> Type[Base]:
        """Получение класса модели для запроса получения данных объекта"""
        return self.model_class

    async def retrieve_post_processing(self, entity_id: int | UUID, item: BaseModel | dict) -> BaseModel | dict:
        """Постобработка данных объекта"""
        return item

    async def retrieve(self, entity_id: int | UUID, image_params: ImageParamSchema = None) -> BaseModelType:
        """Получение данных объекта"""
        statement = await execute_function(self.retrieve_query, entity_id)
        statement_result = await self.session.execute(statement)
        entity = statement_result.scalar()
        if entity is None:
            raise NotFoundException(
                code="entity_not_found",
                message_context={
                    "title": self.model_class.case.nominative,
                    "field_title": "ID",
                    "field_value": entity_id,
                },
                context={"entity_id": entity_id},
            )

        action = stack()[0].function
        model_class = self.retrieve_model_class()
        item = await self.entity_to_schema(entity, model_class, action=action, image_params=image_params)
        result = {"item": await self.retrieve_post_processing(entity_id, item)}
        return self.result_to_schema(action, result, model_class)

    def retrieve_collection_query(self, data: BaseRetrieveCollectionRequest) -> Select:
        """Построение запроса получения коллекции объектов"""
        return select(self.model_class)

    def retrieve_collection_query_order(self, data: BaseRetrieveCollectionRequest, statement: Select) -> Select:
        """Построение сортировки запроса получения коллекции объектов"""
        sort = data.sort or "-updated_on" if hasattr(self.model_class, "updated_on") else "-id"
        sort_order = c.SA_SORT_ORDER_DESC if sort[:1] == "-" else c.SA_SORT_ORDER_ASC
        sort_by = sort[1:] if sort[:1] == "-" else sort
        if hasattr(self.model_class, sort_by):
            column = getattr(self.model_class, sort_by)
            statement = statement.order_by(desc(column) if sort_order == c.SA_SORT_ORDER_DESC else asc(column))

        return statement

    async def retrieve_collection_query_pagination(
        self, data: BaseRetrieveCollectionRequest, statement: Select, model_class: Type[Base] = None
    ) -> tuple[int, int, int]:
        """Построение пагинации запроса получения коллекции объектов"""
        query_count = statement.with_only_columns(label("cnt", func.count(model_class.id))).order_by(None)
        statement_result = await self.session.execute(query_count)
        total = statement_result.scalar()
        offset = (data.page - 1) * data.limit
        pages = int(total / data.limit)
        if data.limit * pages < total:
            pages += 1

        return total, pages, offset

    async def retrieve_collection_filters(
        self, data: BaseRetrieveCollectionRequest | BaseModel
    ) -> tuple[dict[str, list[BinaryExpression]], dict[str, ModelJoinItem]]:
        """
        Получение фильтров коллекции объектов.

        Возвращаются два словаря:

        - первый словарь - содержит два элемента:

          - ключ - `and_` или `or_`
          - значение - список условий фильтрации


        - второй словарь - содержит элементы для объединения таблиц:

          - ключ - имя таблицы, к примеру `ArticleTag.__tablename__`
          - значение - экземпляр класса `ModelJoinItem`

        Пример возвращаемого результата:

        (
            {
                "and_": [ArticleTag.is_fixed_material.is_(True)],
                "or_": [
                    ArticleTag.content_type_id.in_([1, 2]),
                    ArticleTag.tag_id.in_(["tag-1", "tag-2"]),
                ],
            },

            {
                str(ArticleTag.__tablename__): ModelJoinItem(
                    target=ArticleTag, onclause=Article.id == ArticleTag.article_id
                ),
            }
        )

        """
        exclude_fields = [key for key in BaseRetrieveCollectionRequest.model_fields.keys()]
        logger.debug(f"exclude_fields: {repr(exclude_fields)}")

        joins = {}
        filters = defaultdict(list)
        # or_filter_fields = data.or_filter_fields or []
        or_filter_fields = []

        for key in data.model_fields.keys():
            if key in exclude_fields:
                continue

            value = getattr(data, key, None)
            if value is not None:
                attr_filter_method = f"retrieve_collection_filter_{key}"
                if hasattr(self, attr_filter_method):
                    method = getattr(self, attr_filter_method)
                    attr_filters, attr_joins = await execute_function(method, value)
                    if isinstance(attr_joins, dict) and len(attr_joins):
                        joins.update(attr_joins)

                elif hasattr(self.model_class, key):
                    attr = getattr(self.model_class, key)
                    if isinstance(value, list) and len(value):
                        attr_filters = attr.in_(value)
                    elif not isinstance(value, list):
                        attr_filters = attr == value
                    else:
                        continue
                else:
                    continue

                filter_key = "or_" if key in or_filter_fields else "and_"
                if isinstance(attr_filters, list):
                    filters[filter_key].extend(attr_filters)
                else:
                    filters[filter_key].append(attr_filters)

        return filters, joins

    async def build_collection_query(
        self,
        data: BaseRetrieveCollectionRequest,
        get_query: Callable = None,
        get_filters: Callable = None,
        get_order: Callable = None,
    ) -> Select:
        """Построение запроса для получения коллекции объектов"""
        filters, joins = await execute_function_default(get_filters, self.retrieve_collection_filters, data)

        statement = await execute_function_default(get_query, self.retrieve_collection_query, data)

        if len(filters.get("and_", [])):
            statement = statement.where(*filters["and_"])

        if len(filters.get("or_", [])):
            statement = statement.where(or_(*filters["or_"]))

        if len(joins):
            for join_item in joins.values():
                statement = statement.join(**join_item.__dict__)

        return await execute_function_default(get_order, self.retrieve_collection_query_order, data, statement)

    async def retrieve_collection(
        self,
        data: BaseRetrieveCollectionRequest,
        get_query: Callable = None,
        get_filters: Callable = None,
        get_order: Callable = None,
        model_class: Type[Base] = None,
        schema_class: Type[BaseModel] = None,
        with_states: bool = False,
    ) -> dict:
        """Получение коллекции объектов"""
        action = stack()[0].function
        model_class = model_class or self.model_class
        image_params = ImageParamSchema(
            image_width=data.image_width,
            image_height=data.image_height,
            image_format=data.image_format,
        )

        statement = await self.build_collection_query(data, get_query, get_filters, get_order)

        states = await self.retrieve_collection_states(statement) if with_states is True else None

        if self.is_collection_paginate:
            total, pages, offset = await self.retrieve_collection_query_pagination(data, statement, model_class)
            statement = statement.offset(offset).limit(data.limit)
        else:
            total = pages = 0

        statement_result = await self.session.execute(statement)
        items = [
            await self.entity_to_schema(item, model_class, schema_class, action=action, image_params=image_params)
            for item in statement_result.scalars().all()
        ]
        items = await self.retrieve_collection_post_processing(data, items)

        result = (
            {"page": data.page, "limit": data.limit, "pages": pages, "total": total, "items": items}
            if self.is_collection_paginate is True
            else {"items": items}
        )

        if with_states:
            result["states"] = states

        return result

    def get_model_state_column(self, model_class: Type[Base] = None) -> Column | None:
        """Получение поля модели, содержащего значение статуса объекта"""
        model_class = model_class or self.model_class
        column = getattr(model_class, "state_id", None)
        return column if column and isinstance(column.type, (BigInteger, Integer)) else None

    async def retrieve_collection_filter_state_code(
        self, value: list[str]
    ) -> tuple[BinaryExpression | list[BinaryExpression], dict[str, ModelJoinItem]]:
        """Получение фильтра коллекции объектов по коду статуса"""
        column = self.get_model_state_column()
        return column.in_(await self.get_module_state_ids(include_state_codes=value)) if column else [], {}

    async def retrieve_collection_states(self, statement: Select) -> dict:
        """Получение числа объектов коллекции в разрезе статусов"""
        column = self.get_model_state_column()
        if not column:
            return {}

        states = await self.get_module_states()
        data = {state_code: 0 for state_code in states.keys()}
        state_ids = {state.id: state_code for state_code, state in states.items()}

        """
        Изменяем результирующий запрос:
        - заменяем список полей запроса на `state_id, count(id) as cnt`
        - добавляем группировку по полю `state_id`
        - отменяем текущую сортировку
        - добавляем сортировку по полю `state_id`
        """
        state_statement = (
            statement.with_only_columns(column, label("cnt", func.count(self.model_class.id)))
            .group_by(column)
            .order_by(None)
            .order_by(column)
        )
        statement_result = await self.session.execute(state_statement)
        for item in statement_result.all():
            data[state_ids[item.state_id]] = item.cnt

        return data

    async def retrieve_collection_post_processing(
        self, data: BaseRetrieveCollectionRequest, items: list[BaseModel | dict]
    ) -> list[BaseModel | dict]:
        """Постобработка коллекции объектов"""
        return items

    async def entity_check_unique(self, data: BaseModel, entity_id: int | UUID = None):
        """Проверка уникальности объекта"""
        if not isinstance(self.entity_unique_fields, list) or not len(self.entity_unique_fields):
            return

        entity_unique_fields = (
            [self.entity_unique_fields]
            if not isinstance(self.entity_unique_fields[0], list)
            else self.entity_unique_fields
        )

        for unique_fields in entity_unique_fields:
            filters = []
            for field in unique_fields:
                value = getattr(data, field, None)
                if value is None and not self.model_class.__mapper__.columns[field].nullable:
                    filters.append(getattr(self.model_class, field).is_(None))
                elif value is not None:
                    filters.append(getattr(self.model_class, field) == value)

            statement = select(label("cnt", func.count(self.model_class.id)))

            if self.entity_unique_operator.lower() == c.SA_FILTER_OPERATOR_OR:
                statement = statement.where(or_(*filters))
            else:
                statement = statement.where(*filters)

            if (
                self.entity_unique_exclude_states
                and len(self.entity_unique_exclude_states)
                and (column := self.get_model_state_column())
            ):
                statement = statement.where(
                    column.in_(await self.get_module_state_ids(exclude_state_codes=self.entity_unique_exclude_states))
                )

            if entity_id:
                statement = statement.where(self.model_class.id != entity_id)

            statement_result = await self.session.execute(statement)
            record_count = statement_result.scalar()
            if record_count > 0:
                fields = [field for field in unique_fields]
                operator = " || " if self.entity_unique_operator.lower() == c.SA_FILTER_OPERATOR_OR else " & "
                raise ConflictException(
                    code="entity_with_unique_fields_already_exists",
                    message_context={
                        "title": self.model_class.case.nominative,
                        "fields": operator.join([f"{field}={getattr(data, field, None)}" for field in fields]),
                    },
                )

    def entity_create_include_fields(self, data: BaseModel) -> list[str] | None:
        """Получение списка полей, заполняемых при создании объекта"""

    def entity_create_exclude_fields(self, data: BaseModel) -> list[str] | None:
        """Получение списка полей, не заполняемых при создании объекта"""

    def entity_update_include_fields(self, data: BaseModel, entity: Base = None) -> list[str] | None:
        """Получение списка полей, заполняемых при обновлении объекта"""

    def entity_update_exclude_fields(self, data: BaseModel, entity: Base = None) -> list[str] | None:
        """Получение списка полей, не заполняемых при обновлении объекта"""

    def entity_patch_include_fields(self, data: BaseModel, entity: Base = None) -> list[str] | None:
        """Получение списка полей, заполняемых при частичном обновлении объекта"""

    def entity_patch_exclude_fields(self, data: BaseModel, entity: Base = None) -> list[str] | None:
        """Получение списка полей, не заполняемых при частичном обновлении объекта"""

    def update_entity_from_data(self, entity: Base, data: BaseModel, action: str):
        """Обновление данных объекта данными запроса"""
        match action:
            case "create":
                include_fields = self.entity_create_include_fields(data) or []
                exclude_fields = self.entity_create_exclude_fields(data) or []
            case "update":
                include_fields = self.entity_update_include_fields(data, entity) or []
                exclude_fields = self.entity_update_exclude_fields(data, entity) or []
            case "patch":
                include_fields = self.entity_patch_include_fields(data, entity) or []
                exclude_fields = self.entity_patch_exclude_fields(data, entity) or []
            case _:
                include_fields = []
                exclude_fields = []

        for k, v in data.model_dump().items():
            if hasattr(entity, k) and k not in exclude_fields and (len(include_fields) < 1 or k in include_fields):
                setattr(entity, k, v)

    async def entity_validate(self, entity: Base, data: BaseModel, action: str):
        """Валидация данных объекта"""

    async def before_entity_create(self, entity: Base, data: BaseModel):
        """Выполнение дополнительных действий перед созданием объекта"""
        created_by = self.user_id

        if hasattr(self.model_class, "created_by"):
            self.entity_create_additional_fields["created_by"] = created_by

        if hasattr(self.model_class, "updated_by"):
            self.entity_create_additional_fields["updated_by"] = created_by

        if (
            self.get_model_state_column() is not None
            and getattr(entity, "state_id", None) is None
            and self.entity_create_additional_fields.get("state_id") is None
        ):
            state_ids = await self.get_module_state_ids(include_state_codes=self.new_entity_state_code)
            self.entity_create_additional_fields["state_id"] = state_ids[0]

        if isinstance(self.model_class.id.type, postgresql.UUID):
            self.entity_create_additional_fields["id"] = uuid4()

        set_instance_attribute_values(entity, self.entity_create_additional_fields)

    async def after_entity_create(self, entity: Base, data: BaseModel):
        """Выполнение дополнительных действия после создания объекта"""

    async def create(self, data: BaseModel) -> BaseModelType:
        """Создание объекта"""
        action = stack()[0].function

        self.entity_create_additional_fields = {}
        entity: Base = self.model_class()

        await self.entity_check_unique(data)

        self.update_entity_from_data(entity, data, action)

        await self.entity_validate(entity, data, action)

        await self.before_entity_create(entity, data)

        self.session.add(entity)

        await self.flush_and_refresh_entity(entity)

        await self.after_entity_create(entity, data)

        # if self.is_create_event_registration:
        #     await self.get_service(ModuleEvent.__tablename__).registration(entity, action)

        await self.flush_and_refresh_entity(entity)
        action = stack()[0].function
        return await self.entity_to_schema(entity, action=action)

    async def before_entity_update(self, entity: Base, data: BaseModel):
        """Выполнение дополнительных действий перед изменением объекта"""
        if hasattr(self.model_class, "updated_by"):
            self.entity_update_additional_fields["updated_by"] = self.user_id

        set_instance_attribute_values(entity, self.entity_update_additional_fields)

    async def after_entity_update(self, entity: Base, data: BaseModel):
        """Выполнение дополнительных действия после изменения объекта"""

    async def after_entity_patch(self, entity: Base, data: BaseModel):
        """Выполнение дополнительных действия после частичного изменения объекта"""

    async def check_entity_update(self, entity: Base, data: BaseModel):
        """Проверка возможности изменения объекта"""

    async def check_entity_patch(self, entity: Base, data: BaseModel):
        """Проверка возможности частичного изменения объекта"""

    async def update(
        self, entity_id: int | UUID, data: BaseModel, is_partial: bool = None, is_return_response_schema: bool = False
    ) -> BaseModelType:
        """Изменение данных объекта"""
        action = "patch" if is_partial is True else "update"

        self.entity_update_additional_fields = {}
        entity: Base = await self.get_entity_for_update(entity_id)

        if is_partial is True:
            await self.check_entity_patch(entity, data)
        else:
            await self.check_entity_update(entity, data)

        await self.entity_check_unique(data, entity_id)

        """
        Если загружать несуществующие ID внешних ключей в существующую модель,
        то при выполнении запросов получения других моделей в методе валидации
        после выполнения autoflush возникает ошибка `psycopg2.errors.ForeignKeyViolation`.

        Для сохранения возможности использования объектной модели в методе валидации,
        использования единого механизма валидации как при создании, так и при изменении объекта
        реализован следующий механизм:
        - данные запроса обновления загружаются не в существующую модель, а в новую модель, как при создании
        - выполняется валидация данных запроса обновления
        - в случае успешной валидации данные запроса обновления загружаются в существующую модель
        - выполняются последующие действия
        """
        test_entity: Base = self.model_class()
        self.update_entity_from_data(test_entity, data, action)
        await self.entity_validate(test_entity, data, action)

        self.update_entity_from_data(entity, data, action)

        await self.before_entity_update(entity, data)

        await self.flush_and_refresh_entity(entity)

        if is_partial is True:
            await self.after_entity_patch(entity, data)
        else:
            await self.after_entity_update(entity, data)

        # if self.is_create_event_registration:
        #     await self.get_service(ModuleEvent.__tablename__).registration(entity, action)

        await self.flush_and_refresh_entity(entity)
        action = stack()[0].function

        if not is_return_response_schema:
            return await self.entity_to_schema(entity, action=action)

        model_class = self.retrieve_model_class()
        item = await self.entity_to_schema(entity, model_class, action=action)
        result = {"item": await self.retrieve_post_processing(entity_id, item)}
        return self.result_to_schema(action, result, model_class)

    async def check_entity_change_state(
        self, entity: Base, data: BaseChangeStateRequest, current_state: ModuleState, new_state: ModuleState
    ):
        """Проверка возможности изменения статуса объекта"""

    async def before_entity_change_state(
        self, entity: Base, data: BaseChangeStateRequest, current_state: ModuleState, new_state: ModuleState
    ):
        """Выполнение дополнительных действий перед изменением статуса объекта"""
        if hasattr(self.model_class, "updated_by"):
            entity.updated_by = self.user_id

    async def after_entity_change_state(
        self, entity: Base, data: BaseChangeStateRequest, current_state: ModuleState, new_state: ModuleState
    ):
        """Выполнение дополнительных действий после изменением статуса объекта"""

    async def entity_change_state_check_user_access(
        self, entity: Base, data: BaseChangeStateRequest, new_state: ModuleState
    ):
        """
        Проверка полномочий пользователя на изменение статуса объекта.

        Если доступ запрещен, необходимо генерировать исключение с кодом 403.
        """
        if new_state.code not in self.change_state_actions.keys():
            raise ServerErrorException(
                code="entity_new_state_not_in_list_of_available_actions",
                message_context={"new_state": new_state.title},
            )

        action = self.change_state_actions[new_state.code]
        if not isinstance(action, ACSCheckActionTypes):
            raise ServerErrorException(
                code="class_property_invalid_structure",
                message_context={"property_name": "change_state_actions", "class_name": self.__class__.__name__},
            )

        # role_module_actions = await self.get_role_module_actions(self.user_role["id"]) if self.user_role else {}
        # check = action.check(role_module_actions.get(self.model_class.__tablename__))
        # if check is not True:
        #     raise ForbiddenException(
        #         code="user_access_forbidden",
        #         message_context={
        #             "title": (
        #                 f"Изменение статуса {self.model_class.case.genitive.lower()}"
        #                 if new_state.code != c.STATE_DELETED
        #                 else f"Удаление {self.model_class.case.genitive.lower()}"
        #             )
        #         },
        #     )

        if action.is_owner is True and self.check_user_is_entity_owner(entity, self.user_id) is False:
            raise ForbiddenException(
                code="cannot_change_entity_state_for_another_user",
                message_context={
                    "new_state": new_state.title,
                    "title": self.model_class.case.nominative,
                    "id": entity.id,
                },
            )

    async def change_state(self, data: BaseChangeStateRequest) -> BaseModelType:
        """Изменение статуса объекта"""
        action = stack()[0].function

        entity = await self.get_entity(self.model_class, data.entity_id)

        if not self.get_model_state_column():
            raise ConflictException(
                code="entity_state_not_implemented", message_context={"title": self.model_class.case.genitive}
            )

        if not isinstance(self.change_state_transitions, dict):
            raise ConflictException(
                code="class_property_is_not_specified",
                message_context={"property_name": "change_state_transitions", "class_name": self.__class__.__name__},
            )

        if not isinstance(self.change_state_actions, dict):
            raise ServerErrorException(
                code="class_property_is_not_specified",
                message_context={"property_name": "change_state_actions", "class_name": self.__class__.__name__},
            )

        current_state = entity.state

        new_state: ModuleState = await self.get_entity(ModuleState, data.state_id)

        if new_state.module.code != self.get_model_module_code():
            raise UnprocessableEntityException(
                code="entity_module_state_belongs_to_another_module",
                message_context={"id": data.state_id, "title": new_state.module.title},
            )

        if entity.state_id == new_state.id and not self.is_ignore_similar_state:
            raise ConflictException(
                code="entity_state_and_new_state_is_similar",
                message_context={"state": entity.state.title, "new_state": new_state.title},
            )

        if entity.state.code not in self.change_state_transitions.keys():
            raise ConflictException(
                code="entity_state_not_in_allowed_transitions", message_context={"state": entity.state.title}
            )

        if new_state.code not in self.change_state_transitions[entity.state.code]:
            raise ConflictException(
                code="entity_new_state_not_in_allowed_transitions",
                message_context={"state": entity.state.title, "new_state": new_state.title},
            )

        await self.entity_change_state_check_user_access(entity, data, new_state)

        await self.check_entity_change_state(entity, data, current_state, new_state)

        await self.before_entity_change_state(entity, data, current_state, new_state)

        entity.state_id = new_state.id

        await self.flush_and_refresh_entity(entity)

        await self.after_entity_change_state(entity, data, current_state, new_state)

        # if self.is_create_event_registration:
        #     await self.get_service(ModuleEvent.__tablename__).registration(entity, action)

        await self.flush_and_refresh_entity(entity)
        action = stack()[0].function
        return await self.entity_to_schema(entity, action=action)

    async def check_entity_delete(self, entity: Base, data: BaseDeleteRequest):
        """Проверка возможности удаления объекта"""

    async def delete(self, data: BaseDeleteRequest) -> BaseModelType:
        """Удаление объекта"""
        states = await self.get_module_states()

        entity: Base = await self.get_entity_for_delete(data.entity_id)

        state_column = self.get_model_state_column()

        # Установлен флаг физического удаления и отсутствует поле `state_id` - вызываем метод `physical_delete`
        if self.is_physical_delete is True and not state_column:
            return await self.physical_delete(entity, data)

        if not state_column or c.STATE_DELETED not in states.keys():
            raise ConflictException(
                code="entity_state_deleted_not_implemented", message_context={"title": self.model_class.case.nominative}
            )

        state_deleted: ModuleState = states.get(c.STATE_DELETED)

        if entity.state_id == state_deleted.id:
            raise ConflictException(
                code="entity_already_deleted",
                message_context={"id": entity.id, "title": self.model_class.case.genitive},
            )

        await self.check_entity_delete(entity, data)

        return await self.change_state(BaseChangeStateRequest(entity_id=data.entity_id, state_id=state_deleted.id))

    async def entity_physical_delete_check_user_access(self, entity: Base, data: BaseDeleteRequest):
        """
        Проверка полномочий пользователя для физического удаления объекта.

        Если доступ запрещен, необходимо генерировать исключение с кодом 403.
        """
        if hasattr(entity, "user_id") and self.check_user_is_entity_owner(entity, self.user_id) is False:
            raise ForbiddenException(
                code="physical_delete_entity_error",
                message_context={
                    "title": entity.case.nominative,
                    "id": entity.id,
                    "error": "владельцем объекта является другой пользователь",
                },
            )

    async def check_entity_physical_delete(self, entity: Base, data: BaseDeleteRequest):
        """Проверка возможности физического удаления объекта"""

    async def before_entity_physical_delete(self, entity: Base, data: BaseDeleteRequest):
        """Выполнение дополнительных действий перед физическим удалением объекта"""

    async def after_entity_physical_delete(self, entity_data: BaseModel, data: BaseDeleteRequest):
        """Выполнение дополнительных действий после физическое удаления объекта"""

    async def physical_delete(self, entity: Base, data: BaseDeleteRequest) -> BaseModelType:
        """Физическое удаление объекта"""
        action = stack()[0].function

        await self.entity_physical_delete_check_user_access(entity, data)

        await self.check_entity_physical_delete(entity, data)

        await self.before_entity_physical_delete(entity, data)

        entity_data = await self.entity_to_schema(entity, action=action)
        # entity_event_title = entity.get_event_title()
        # entity_module_code = self.get_model_module_code(type(entity))

        try:
            statement = delete(self.model_class).where(self.model_class.id == entity.id)
            await self.session.execute(statement)
        except Exception as e:
            raise ConflictException(
                code="physical_delete_entity_error",
                message_context={
                    "title": entity.case.nominative,
                    "id": entity.id,
                    "error": (
                        "имеются связанные объекты"
                        if isinstance(e, IntegrityError) and e.orig.pgcode == FOREIGN_KEY_VIOLATION
                        else str(e)
                    ),
                },
            )

        await self.after_entity_physical_delete(entity_data, data)

        # if self.is_delete_event_registration:
        #     module: Module = self.get_entity(Module, entity_module_code, "code", "code")
        #     await self.get_service(ModuleEvent.__tablename__).registration_from_data(
        #         entity_data, action, module.id, entity_event_title
        #     )

        await self.commit_and_refresh_entity()

        return entity_data

    ###############################

    # async def check_event_access(self, module_code: str, action_code: str, role_id: int) -> bool:
    #     """Проверка доступности события для текущей роли пользователя"""
    #     module_actions = await self.get_role_module_actions(role_id)
    #     return module_code in module_actions.keys() and action_code in module_actions[module_code]


BaseServiceType = TypeVar("BaseServiceType", bound=BaseService)
