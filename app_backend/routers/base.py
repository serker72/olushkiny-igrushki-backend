import json
from datetime import datetime
from enum import Enum
from functools import wraps
from inspect import stack
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Sequence, Type, TypeVar
from uuid import UUID

from classy_fastapi import Routable
from fastapi import Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Boolean, Enum
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils import Ltree
from starlette.datastructures import URL
from starlette_wtf import StarletteForm, csrf_protect

from app_backend.services.base import BaseServiceType, ServiceManager
from common.exceptions import ConflictException, MethodNotAllowedException, UnprocessableEntityException

# from common.helpers.string import name_plural_to_singular
from common.helpers import constants as c
from common.helpers import timeutil
from common.helpers.classes import BaseObject
from common.helpers.database import get_request_sa_session
from common.helpers.dict import object_to_dict
from common.helpers.file import check_file_exists
from common.helpers.function import execute_function
from common.helpers.template import url_for
from common.models import Base, ModuleState, User
from common.schemas.models import BackendSettings, BaseModelType
from common.schemas.requests.base import BaseRetrieveCollectionRequest
from common.schemas.responses.base import CustomJSONResponse


def base_router_initial_service(f):
    """Декоратор методов базового преставления для инициализации экземпляра класса сервиса"""

    @wraps(f)
    async def async_wrapper(*args, **kwargs):
        logger.debug(f"args: {repr(args)}, kwargs: {repr(kwargs)}")
        instance: BaseRouter = args[0]
        request: Request = args[1] if len(args) > 1 else kwargs.get("request")
        instance.service = instance.get_service(f.__name__, request)
        return await f(*args, **kwargs)

    return async_wrapper


class GridColumnType(str, Enum):
    boolean = "boolean"
    currency = "currency"
    default = "default"
    datetime = "datetime"
    enum = "enum"
    relation = "relation"
    virtual = "virtual"
    virtual_with_context = "virtual_with_context"
    json = "json"
    json_in_modal = "json_in_modal"


class GridColumn(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    title: str
    field: str = None
    content: str = None
    col_type: str = GridColumnType.default
    is_sorted: bool = False
    foreign_field: str = None
    related_field: str = None
    is_filtered: bool = False
    is_filter_multiple: bool = False
    filter_items: dict = {}
    # user_account_types: list[int] = []
    modal_header: str = None


class GridPagination(BaseObject):
    """Класс пагинатора списка объектов"""

    page: int
    limit: int
    offset: int
    total: int
    total_pages: int
    inner_window: int = 2
    outer_window: int = 1

    @property
    def pages(self) -> range | list[int]:
        """Список отображаемых страниц"""
        if self.total_pages < self.inner_window * 2 - 1:
            return range(1, self.total_pages + 1)

        pages = []
        win_from = self.page - self.inner_window
        win_to = self.page + self.inner_window
        if win_to > self.total_pages:
            win_from -= win_to - self.total_pages
            win_to = self.total_pages

        if win_from < 1:
            win_to = win_to + 1 - win_from
            win_from = 1
            if win_to > self.total_pages:
                win_to = self.total_pages

        if win_from > self.inner_window:
            pages.extend(range(1, self.outer_window + 1 + 1))
            pages.append(None)
        else:
            pages.extend(range(1, win_to + 1))

        if win_to < self.total_pages - self.inner_window + 1:
            if win_from > self.inner_window:
                pages.extend(range(win_from, win_to + 1))

            pages.append(None)
            if self.outer_window == 0:
                pages.extend(range(self.total_pages, self.total_pages + 1))
            else:
                pages.extend(range(self.total_pages - 1, self.total_pages + 1))

        elif win_from > self.inner_window:
            pages.extend(range(win_from, self.total_pages + 1))
        else:
            pages.extend(range(win_to + 1, self.total_pages + 1))

        return pages

    @property
    def has_prev(self) -> bool:
        """Флаг наличия предыдущей страницы"""
        return self.page > 1

    @property
    def has_next(self) -> bool:
        """Флаг наличия следующей страницы"""
        return self.page < self.total_pages

    @property
    def page_prev(self) -> int:
        """Номер предыдущей страницы"""
        return self.page - 1 if self.page > 1 else 1

    @property
    def page_next(self) -> int:
        """Номер следующей страницы"""
        return self.page + 1 if self.page < self.total_pages else self.total_pages

    @property
    def page_first_item(self) -> int:
        """Номер первой записи на текущей странице"""
        return (self.page - 1) * self.limit + 1 if self.page > 1 else 1

    @property
    def page_last_item(self) -> int:
        """Номер последней записи на текущей странице"""
        return (self.page - 1) * self.limit + self.limit if self.page < self.total_pages else self.total


class BaseRouter(Routable):
    """Класс базового представления"""

    prefix: str = None
    tags: list[str] = None
    service_manager: ServiceManager = None
    service: BaseServiceType = None
    settings: BackendSettings = None
    # user: User = None
    not_cached_endpoints: list[str] = None
    without_database_endpoints: list[str] = None
    is_security_dependency: bool = True
    security_dependency_endpoints: list[str] = None

    def __init__(self, service_manager: ServiceManager, **kwargs) -> None:
        """Конструктор класса"""
        self.service_manager = service_manager
        self.settings = kwargs.pop("settings", None)
        super().__init__(prefix=self.prefix, tags=self.tags, **kwargs)

    def get_module_code(self) -> str:
        """Получение кода модуля из префикса"""
        module_code = self.prefix.strip("/").replace("-", "_")
        # return f"{module_code[:-3]}y" if module_code.endswith("ies") else module_code[:-1]
        # return name_plural_to_singular(module_code)
        return module_code

    def get_service(self, method_name: str, request: Request, module_code: str = None) -> BaseServiceType:
        """Получение экземпляра класса сервиса"""
        logger.debug(f"session={get_request_sa_session(request)}, method_name={method_name}")

        return self.service_manager.get_service(
            module_code=module_code or self.get_module_code(),
            request_id=request.state.request_id,
            user_agent=request.state.user_agent,
            user_id=getattr(request.state, "user_id", None),
            user_time_zone=getattr(request.state, "user_time_zone", None),
            session=getattr(request.state, "sa_session", None),
            view_action=method_name,
        )


# class BaseAPIRouter(BaseRouter):
#     """Класс базового представления API"""


class BaseUIRouter(BaseRouter):
    """Класс базового представления UI"""

    templates: Jinja2Templates = None
    model_class: Type[Base] = None

    create_form: Type[StarletteForm] = None
    update_form: Type[StarletteForm] = None

    create_schema: Type[BaseModel] = None
    update_schema: Type[BaseModel] = None

    parent_entity_prefix: str = None
    parent_entity_id_name: str = None
    parent_entity_id: int | UUID = None

    is_created: bool = True
    is_updated: bool = True
    is_view: bool = True
    is_view_in_modal: bool = False
    is_view_and_updated: bool = True
    is_deleted: bool = False
    is_virtual_deleted: bool = False
    is_show_filters: bool = True
    is_show_custom_search_string_filter: bool = False

    is_partial_template: bool = False
    is_exported: bool = False

    grid_default_order: str = "-id"
    grid_export_template: str = "grid.xlsx"

    boolean_choices: list[tuple] = [("0", "Нет"), ("1", "Да")]
    boolean_items: dict = {"0": "Нет", "1": "Да"}

    template_additional_buttons: str = None
    template_common_directory: str = "page/common"
    template_partial_directory: str = None
    java_script: str = None

    def __init__(self, service_manager: ServiceManager, **kwargs) -> None:
        """Конструктор класса"""
        self.service_manager = service_manager
        self.templates = kwargs.pop("templates", None)
        super().__init__(service_manager, **kwargs)

    @property
    def template_aliases(self) -> dict:
        """Словарь соответствия алиасов и имен файлов шаблонов"""
        return {
            "list_page": f"{self.template_common_directory}/index.html",
            "grid_body": f"{self.template_common_directory}/blocks/_grid_body.html",
            "grid_pagination": f"{self.template_common_directory}/blocks/_grid_pagination.html",
            "create_page": f"{self.template_common_directory}/create.html",
            "update_page": f"{self.template_common_directory}/update.html",
            "view_page": f"{self.template_common_directory}/view.html",
            "view_in_modal_page": f"{self.template_common_directory}/view_in_modal.html",
        }

    async def get_template_common_context(self, request: Request) -> dict:
        """Получение словаря общих данных для шаблонов страниц"""
        user_service = self.get_service(stack()[0].function, request, c.MODULE_CODE_USERS)
        user = (
            await user_service.get_entity(user_service.model_class, request.state.user_id)
            if hasattr(request.state, "user_id")
            else None
        )
        return {
            "request": request,
            "java_script": self.java_script,
            "settings": object_to_dict(self.settings),
            "titles": self.get_titles() if self.model_class else {},
            # "user": object_to_dict(self.user),
            "user": await user.as_dict(1) if user else None,
            "is_created": self.is_created,
            "is_updated": self.is_updated,
            "is_view": self.is_view,
            "is_view_in_modal": self.is_view_in_modal,
            "is_view_and_updated": self.is_view_and_updated,
            "is_deleted": self.is_deleted,
            "is_show_filters": self.is_show_filters,
            "list_page_url": self.get_list_url(request, "page"),
            "list_api_url": self.get_list_url(request, "api"),
            "create_page_url": self.get_create_url(request, "page"),
            "create_api_url": self.get_create_url(request, "api"),
            "view_page_url": self.get_view_url(request),
            "view_in_modal_page_url": self.get_view_in_modal_url(request),
            "view_page_url_params": self.get_view_url_params(request),
            "update_page_url": self.get_update_url(request, "page"),
            "update_api_url": self.get_update_url(request, "api"),
            "view_and_update_page_url": self.get_view_and_update_url(request),
            "delete_api_url": self.get_delete_url(request, "api"),
            "delete_all_api_url": self.get_delete_all_url(request, "api"),
            "parent_entity_view_and_update_page_url": self.get_parent_entity_view_and_update_url(request),
            "is_partial_template": self.is_partial_template,
        }

    async def get_template_additional_context(self, request: Request, action: str) -> dict:
        """Получение словаря дополнительных данных для указанного шаблона страницы"""
        return {}

    async def build_template_context(self, request: Request, action: str, template_context: dict) -> dict:
        """Получение словаря данных для шаблонов страниц"""
        template_common_context = await self.get_template_common_context(request)
        if isinstance(template_common_context, dict) and len(template_common_context):
            template_context.update(template_common_context)

        template_additional_context = await self.get_template_additional_context(request, action)
        if isinstance(template_additional_context, dict) and len(template_additional_context):
            template_context.update(template_additional_context)

        # logger.debug(f"template_context: {repr(template_context)}")
        return template_context

    async def build_template_response(self, request: Request, action: str, template_context: dict) -> HTMLResponse:
        """Построение ответа на основе шаблона Jinja"""
        return self.templates.TemplateResponse(
            request,
            self.template_aliases.get(action),
            context=await self.build_template_context(request, action, template_context),
        )

    async def get_common_columns(self) -> dict[str, GridColumn]:
        """Получение списка общих колонок"""
        columns = {}

        if hasattr(self.model_class, "id"):
            columns["id"] = GridColumn(field="id", title="ID", is_sorted=True)

        if hasattr(self.model_class, "created_on"):
            columns["created_on"] = GridColumn(
                field="created_on",
                title="Время создания",
                col_type=GridColumnType.datetime,
                is_filtered=False,
                is_sorted=True,
            )

        if hasattr(self.model_class, "updated_on"):
            columns["updated_on"] = GridColumn(
                field="updated_on",
                title="Время обновления",
                col_type=GridColumnType.datetime,
                is_filtered=False,
                is_sorted=True,
            )

        if hasattr(self.model_class, "state_id"):
            columns["state_id"] = GridColumn(
                field="state_id",
                title="Статус",
                col_type=GridColumnType.relation,
                foreign_field="state",
                related_field="title",
                is_filtered=True,
                filter_items=await self.service.get_dictionary_items(
                    model_class=ModuleState,
                    field_title="title",
                    filters=[ModuleState.hierarchy.descendant_of(Ltree(self.get_module_code()))],
                ),
                is_sorted=True,
            )

        if self.is_show_custom_search_string_filter:
            columns["custom_search_string"] = GridColumn(
                field="custom_search_string",
                title="Произвольная строка поиска",
                is_filtered=True,
            )

        return columns

    async def get_columns(self) -> dict[str, GridColumn]:
        """Получение списка общих колонок"""
        return {}

    async def get_all_columns(self) -> dict[str, GridColumn]:
        """Получение списка общих колонок"""
        columns = await self.get_common_columns()
        columns.update(await self.get_columns())
        return columns

    def get_grid_column_keys(self) -> list[str]:
        """Получение списка наименований колонок для списка"""
        return []

    async def get_grid_columns(self, column_list_method_name: str = "get_grid_column_keys") -> list[GridColumn]:
        """Получение списка колонок для списка"""
        if not hasattr(self, column_list_method_name):
            raise MethodNotAllowedException(
                code="class_method_not_implemented",
                message_context={"method_name": column_list_method_name, "class_name": self.__class__.__name__},
            )

        columns = await self.get_all_columns()
        grid_columns = []
        for k in getattr(self, column_list_method_name)():
            column = columns[k]
            # if not len(column.user_account_types) or self.user.account_type in column.user_account_types:
            grid_columns.append(column)

        return grid_columns

    async def get_grid_filter_columns(self) -> list[GridColumn]:
        """Получение списка колонок для фильтрации списка"""
        columns = await self.get_all_columns()
        return [v for k, v in columns.items() if v.is_filtered is True]

    async def get_view_columns(self) -> list[GridColumn]:
        """Получение списка колонок для страницы просмотра"""
        columns = await self.get_all_columns()
        return [v for k, v in columns.items() if k != "id"]

    def get_grid_default_order(self) -> str:
        """Получение поля для сортировки списка объектов по умолчанию"""
        return (
            "-updated_on"
            if hasattr(self.model_class, "updated_on") and self.grid_default_order == "-id"
            else self.grid_default_order
        )

    def get_titles(self, action: str = None) -> dict:
        """Получение наименований"""
        return {
            "headers": {
                "page_index": f"Список {self.model_class.case.plural_genitive.lower()}",
                "page_create": f"Создание {self.model_class.case.genitive.lower()}",
                "page_update": f"Изменение данных {self.model_class.case.genitive.lower()}",
                "page_view": f"Просмотр данных {self.model_class.case.genitive.lower()}",
                "view_and_update": f"Управление {self.model_class.case.instrumental.lower()}",
                "page_delete": f"Удаление {self.model_class.case.genitive.lower()}",
            },
            "buttons": {
                "button_create": f"Добавить {self.model_class.case.accusative.lower()}",
                "button_update": f"Изменение данных {self.model_class.case.genitive.lower()}",
                "button_view": f"Просмотр данных {self.model_class.case.genitive.lower()}",
                "button_delete": f"Удалить {self.model_class.case.accusative.lower()}",
                "button_export": "Экспорт списка в xlsx",
            },
            "links": {
                "page_index": f"К списку {self.model_class.case.plural_genitive.lower()}",
            },
        }

    def get_url_context(self, request: Request, path: str) -> dict:
        """Получение словаря параметров для формирования URL"""
        context = {"path": path}

        if self.parent_entity_id is not None:
            context[self.parent_entity_id_name] = self.parent_entity_id

        if self.is_partial_template:
            context["is_partial_template"] = True

        context["is_ignored_query_params"] = True

        return context

    def get_list_url(self, request: Request, suffix: str) -> URL | str:
        """Получение ссылки для страницы со списком объектов"""
        return url_for({"request": request}, self.prefix, **self.get_url_context(request, f"/list/{suffix}"))

    def get_create_url(self, request: Request, suffix: str) -> URL | str:
        """Получение ссылки для создания объекта"""
        return url_for({"request": request}, self.prefix, **self.get_url_context(request, f"/create/{suffix}"))

    def get_view_url(self, request: Request) -> URL | str:
        """Получение ссылки для просмотра объекта"""
        return url_for({"request": request}, self.prefix, **self.get_url_context(request, "/view/page"))

    def get_view_in_modal_url(self, request: Request) -> URL | str:
        """Получение ссылки для просмотра объекта в модальном окне"""
        return url_for({"request": request}, self.prefix, **self.get_url_context(request, "/view-in-modal/page"))

    def get_view_url_params(self, request: Request) -> dict:
        """Получение дополнительных параметров ссылки для просмотра объекта"""
        return {}

    def get_update_url(self, request: Request, suffix: str) -> URL | str:
        """Получение ссылки для изменения объекта"""
        return url_for({"request": request}, self.prefix, **self.get_url_context(request, f"/update/{suffix}"))

    def get_delete_url(self, request: Request, suffix: str) -> URL | str:
        """Получение ссылки для удаления объекта"""
        return url_for({"request": request}, self.prefix, **self.get_url_context(request, f"/delete/{suffix}"))

    def get_delete_all_url(self, request: Request, suffix: str) -> URL | str:
        """Получение ссылки для удаления всех объектов"""
        return url_for({"request": request}, self.prefix, **self.get_url_context(request, f"/delete-all/{suffix}"))

    def get_view_and_update_url(self, request: Request) -> URL | str:
        """Получение ссылки для просмотра и изменения объекта"""
        return url_for({"request": request}, self.prefix, **self.get_url_context(request, "/view-and-update/page"))

    def get_parent_entity_view_and_update_url(self, request: Request) -> URL | str:
        """Получение ссылки для просмотра и изменения объекта"""
        return (
            url_for(
                {"request": request},
                self.parent_entity_prefix,
                path="/view-and-update/page",
                entity_id=self.parent_entity_id,
                is_ignored_query_params=True,
            )
            if self.parent_entity_prefix is not None and self.parent_entity_id is not None
            else ""
        )

    def get_view_and_update_url_params(self, request: Request) -> dict:
        """Получение дополнительных параметров ссылки для просмотра и изменения объекта"""
        return {}

    async def create_form_fill(self, form: StarletteForm):
        """Установка значений отдельных полей формы создания объекта"""

    async def update_form_fill(self, form: StarletteForm, entity: Base):
        """Установка значений отдельных полей формы изменения объекта"""

    async def entity_to_form(self, form: StarletteForm, entity: Base):
        """Установка значений отдельных полей формы изменения объекта"""
        for field in form:
            if field.name not in ["csrf_token"] and hasattr(entity, field.name):
                field_value = getattr(entity, field.name)
                if isinstance(getattr(self.model_class, field.name).type, Boolean):
                    field.data = "-1" if field_value is None else ["0", "1"][field_value]
                elif isinstance(getattr(self.model_class, field.name).type, Enum):
                    field.data = field_value.name
                elif isinstance(getattr(self.model_class, field.name).type, postgresql.JSONB):
                    field.data = (
                        json.dumps(getattr(entity, field.name), ensure_ascii=False, indent=2)
                        if field_value is not None
                        else {}
                    )
                elif field.type == "SelectField" and isinstance(field_value, UUID):
                    field.data = str(field_value)
                else:
                    field.data = field_value

                # if "disabled" not in field.render_kw:
                #     field.render_kw["disabled"] = not self.check_user_access("update")

    def get_form_data(self, form: StarletteForm) -> dict:
        """Получение словаря с данными формы создания/изменения объекта"""
        data = {k: v for k, v in form.data.items() if k != "csrf_token"}

        if self.parent_entity_id is not None and self.parent_entity_id_name not in data.keys():
            data[self.parent_entity_id_name] = self.parent_entity_id

        return data

    @base_router_initial_service
    async def list_page(self, request: Request, request_data: BaseRetrieveCollectionRequest) -> HTMLResponse:
        """Получение списка объектов"""
        action = stack()[0].function

        default_order = self.get_grid_default_order()

        template_context = {
            "titles": self.get_titles(action),
            "columns": await self.get_grid_columns(),
            "filter_columns": await self.get_grid_filter_columns(),
            "filter_values": request_data.model_dump(),
            "order": default_order.lstrip("-"),
            "direction": "down" if default_order.startswith("-") else "up",
            "template_additional_buttons": self.template_additional_buttons,
        }
        logger.debug(f"template_context: {repr(template_context)}")

        return await self.build_template_response(request, action, template_context)

    @base_router_initial_service
    async def list_api(
        self, request: Request, request_data: BaseRetrieveCollectionRequest, get_java_script_context: Callable = None
    ) -> CustomJSONResponse | FileResponse:
        """Загрузка списка объектов"""
        action = stack()[0].function

        result = await self.service.retrieve_collection(request_data)
        logger.debug(f"result: {repr(result)}")

        # Экспорт данных - формирование xlsx по шаблону и возврат результирующего файла
        # if request_data.is_export:
        #     if not self.is_exported:
        #         raise ConflictException(
        #             code="list_export_not_implemented", message_context={"name": self.model_class.case.plural_genitive}
        #         )
        #
        #     dt = timeutil.utcnow()
        #     template_file_name = get_template_name_by_user_locale(
        #         f"{LocaleType.russian.value}/{self.template_partial_directory}/{self.grid_export_template}",
        #         self.get_user_locale(),
        #     )
        #     template_file_path = join(BASE_PATH, "payportal", "templates", template_file_name)
        #     if not check_file_exists(template_file_path):
        #         raise ConflictException(code="template_file_not_exists", message_context={"name": template_file_name})
        #
        #     items = []
        #     for item in result.get("items"):
        #         for key in item.model_fields.keys():
        #             value = getattr(item, key)
        #             if isinstance(value, datetime):
        #                 setattr(item, key, format_datetime(get_datetime_as_timezone(value, self.user.timezone)))
        #
        #         logger.debug(f"item: {item.model_dump()}")
        #         items.append(item)
        #
        #     template_context = await self.build_template_context(
        #         request,
        #         action,
        #         {
        #             "d_current": format_datetime(get_datetime_as_timezone(dt, self.user.timezone)),
        #             "items": items,
        #         },
        #     )
        #
        #     with NamedTemporaryFile(
        #         prefix=f"export_{self.template_partial_directory}_{self.user.id}_",
        #         suffix=".xlsx",
        #         delete=False,
        #     ) as file:
        #         render_and_save_template_xlsx(
        #             template_file_path,
        #             file.name,
        #             payloads=[template_context],
        #             jinja_filters=self.templates.env.filters,
        #         )
        #         file.close()
        #
        #         return FileResponse(
        #             file.name,
        #             filename=f"export_{self.template_partial_directory}.xlsx",
        #             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        #         )

        pagination = GridPagination(
            page=request_data.page,
            limit=request_data.limit,
            total=result.get("total", 0),
            total_pages=result.get("pages", 0),
        )
        logger.debug(f"GridPagination: {repr(pagination.__dict__)}")
        logger.debug(f"GridPagination: {repr(pagination.pages)}")

        template_context = {
            "columns": await self.get_grid_columns(),
            "items": result.get("items"),
        }

        template_context = await self.build_template_context(request, action, template_context)
        template = self.templates.get_template(self.template_aliases.get("grid_body"))
        body_html = template.render(template_context)

        template = self.templates.get_template(self.template_aliases.get("grid_pagination"))
        pagination_html = (
            template.render(pagination=pagination, settings=self.settings) if result.get("total") is not None else ""
        )

        java_script_context = (
            await execute_function(get_java_script_context, result.get("items"))
            if callable(get_java_script_context)
            else None
        )

        return CustomJSONResponse(
            {
                "total": result.get("total", 0),
                "body": body_html,
                "pagination": pagination_html,
                "order": request_data.sort,
                "direction": "down" if request_data.sort.startswith("-") else "up",
                "java_script_context": java_script_context,
            }
        )

    @base_router_initial_service
    @csrf_protect
    async def create_page(self, request: Request) -> HTMLResponse:
        """Создание нового объекта"""
        action = stack()[0].function

        if not self.create_form and hasattr(self, "get_create_form_class"):
            self.create_form = await self.get_create_form_class()

        logger.debug(f"self.create_form: {repr(self.create_form)}")

        form = await self.create_form.from_formdata(request)
        await self.create_form_fill(form)

        template_context = {"form": form}

        return await self.build_template_response(request, action, template_context)

    @base_router_initial_service
    @csrf_protect
    async def create_api(self, request: Request) -> BaseModelType:
        """Создание нового объекта"""
        if not self.create_form and hasattr(self, "get_create_form_class"):
            self.create_form = await self.get_create_form_class()

        logger.debug(f"self.create_form: {repr(self.create_form)}")

        form = await self.create_form.from_formdata(request)
        await self.create_form_fill(form)

        if await form.validate_on_submit():
            data = self.get_form_data(form)

            # Вызов метода сервиса
            result = await self.service.create(self.create_schema(**data))
            return result
        else:
            logger.debug(f"form.errors: {repr(form.errors)}")
            raise UnprocessableEntityException(code="invalid_form_field_values", context=form.errors)

    @base_router_initial_service
    @csrf_protect
    async def update_page(self, request: Request, entity_id: int | UUID, is_partial_template: bool) -> HTMLResponse:
        """Изменение объекта"""
        action = stack()[0].function

        entity = await self.service.get_entity(self.model_class, entity_id)

        if not self.update_form and hasattr(self, "get_update_form_class"):
            self.update_form = await self.get_update_form_class(entity)

        await self.service.load_parent_entity()

        form = await self.update_form.from_formdata(request)
        await self.update_form_fill(form, entity)
        await self.entity_to_form(form, entity)

        template_context = {"form": form}

        return await self.build_template_response(request, action, template_context)

    @base_router_initial_service
    @csrf_protect
    async def update_api(self, request: Request, entity_id: int | UUID) -> BaseModelType:
        """Изменение объекта"""
        entity = await self.service.get_entity(self.model_class, entity_id)

        if not self.update_form and hasattr(self, "get_update_form_class"):
            self.update_form = await self.get_update_form_class(entity)

        await self.service.load_parent_entity()

        form = await self.update_form.from_formdata(request)
        await self.update_form_fill(form, entity)

        if await form.validate_on_submit():
            data = self.get_form_data(form)

            # Вызов метода сервиса
            result = await self.service.update(entity_id, self.update_schema(**data))
            return result
        else:
            raise UnprocessableEntityException(code="invalid_form_field_values", context=form.errors)

    async def view_common_page(self, request: Request, entity_id: int | UUID, action: str) -> HTMLResponse:
        """Просмотр данных объекта"""
        entity = await self.service.get_entity(self.model_class, entity_id)
        columns = await self.get_all_columns()

        template_context = {
            "columns": columns.values(),
            "item": entity,
        }

        return await self.build_template_response(request, action, template_context)

    @base_router_initial_service
    async def view_page(self, request: Request, entity_id: int | UUID) -> HTMLResponse:
        """Просмотр данных объекта"""
        action = stack()[0].function
        return await self.view_common_page(request, entity_id, action)

    @base_router_initial_service
    async def view_in_modal_page(self, request: Request, entity_id: int | UUID) -> HTMLResponse:
        """Просмотр данных объекта в модальном окне"""
        action = stack()[0].function
        return await self.view_common_page(request, entity_id, action)
