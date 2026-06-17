from typing import Annotated

from classy_fastapi import Routable, get, post, put
from fastapi import Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from loguru import logger

from app_backend.forms.properties import PropertyCreateForm, PropertyUpdateForm
from app_backend.routers.base import BaseUIRouter, GridColumn, GridColumnType
from common.enums import FlagStatus
from common.models import Module, Property
from common.schemas.models import BaseModelType
from common.schemas.requests import PropertyCreateRequest, PropertyRetrieveCollectionRequest, PropertyUpdateRequest
from common.schemas.responses.base import CustomJSONResponse


class PropertyUIRouter(BaseUIRouter, Routable):
    """Класс представления UI для категорий"""

    prefix = "/properties"
    tags = ["Свойства объектов модулей"]
    is_security_dependency = True
    model_class = Property
    create_form = PropertyCreateForm
    update_form = PropertyUpdateForm
    create_schema = PropertyCreateRequest
    update_schema = PropertyUpdateRequest

    is_view_and_updated = False
    is_updated = True
    is_view = False
    is_view_in_modal: bool = True

    async def get_columns(self) -> dict[str, GridColumn]:
        """Получение списка общих колонок"""
        flag_statuses = {v[0]: v[1] for v in FlagStatus.values()}
        return {
            "module_id": GridColumn(
                field="module_id",
                title="Модуль",
                col_type=GridColumnType.relation,
                foreign_field="module",
                related_field="title",
                is_filtered=True,
                filter_items=await self.service.get_dictionary_items(
                    model_class=Module, field_title="title", filters=[Module.is_used_entity_properties.is_(True)]
                ),
                is_sorted=True,
            ),
            "name": GridColumn(
                field="name",
                title="Наименование",
                is_sorted=True,
            ),
            "is_required": GridColumn(
                field="is_required",
                title="Флаг обязательности",
                col_type=GridColumnType.boolean,
                is_filtered=True,
                filter_items=flag_statuses,
                is_sorted=True,
            ),
            "is_active": GridColumn(
                field="is_active",
                title="Флаг активности",
                col_type=GridColumnType.boolean,
                is_filtered=True,
                filter_items=flag_statuses,
                is_sorted=True,
            ),
        }

    def get_grid_column_keys(self) -> list[str]:
        """Получение списка наименований колонок для списка"""
        return [
            "id",
            "module_id",
            "name",
            "is_required",
            "is_active",
            "updated_on",
        ]

    async def create_form_fill(self, form: PropertyCreateForm):
        """Установка значений отдельных полей формы создания объекта"""
        form.module_id.choices = await self.service.get_dictionary_items(
            model_class=Module,
            field_title="title",
            as_list_of_tuples=True,
            filters=[Module.is_used_entity_properties.is_(True)],
        )
        form.is_required.choices = FlagStatus.values()

    async def update_form_fill(self, form: PropertyUpdateForm, entity: Property):
        """Установка значений отдельных полей формы изменения объекта"""
        await self.create_form_fill(form)
        form.is_active.choices = FlagStatus.values()

    @get("/list/page")
    async def list_page(
        self,
        request: Request,
        request_data: Annotated[PropertyRetrieveCollectionRequest, Query()],
    ) -> HTMLResponse:
        """Получение списка объектов"""
        return await super().list_page(request, request_data)

    @get("/list/api")
    async def list_api(
        self,
        request: Request,
        request_data: Annotated[PropertyRetrieveCollectionRequest, Query()],
    ) -> CustomJSONResponse | FileResponse:
        """Получение списка объектов"""
        logger.debug(f"request_data: {repr(request_data.model_dump())}")
        return await super().list_api(request, request_data)

    @get("/create/page")
    async def create_page(self, request: Request) -> HTMLResponse:
        """Создание нового объекта"""
        return await super().create_page(request)

    @post("/create/api")
    async def create_api(self, request: Request) -> BaseModelType:
        """Создание нового объекта"""
        return await super().create_api(request)

    @get("/update/page")
    async def update_page(self, request: Request, entity_id: int, is_partial_template: bool) -> HTMLResponse:
        """Изменение объекта"""
        return await super().update_page(request, entity_id, is_partial_template)

    @put("/update/api")
    async def update_api(self, request: Request, entity_id: int) -> BaseModelType:
        """Изменение объекта"""
        return await super().update_api(request, entity_id)

    @get("/view-in-modal/page")
    async def view_in_modal_page(self, request: Request, entity_id: int) -> HTMLResponse:
        """Просмотр данных объекта в модальном окне"""
        return await super().view_in_modal_page(request, entity_id)
