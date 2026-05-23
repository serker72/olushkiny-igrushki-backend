from typing import Annotated

from classy_fastapi import Routable, get, post, put
from fastapi import Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy_utils import Ltree

from app_backend.forms.categories import CategoryCreateForm, CategoryUpdateForm
from app_backend.routers.base import BaseUIRouter, GridColumn
from common.models import Category, ModuleState
from common.schemas.models import BaseModelType
from common.schemas.requests import CategoryCreateRequest, CategoryRetrieveCollectionRequest, CategoryUpdateRequest
from common.schemas.responses.base import CustomJSONResponse


class CategoryUIRouter(BaseUIRouter, Routable):
    """Класс представления UI для категорий"""

    prefix = "/categories"
    tags = ["Категории"]
    is_security_dependency = True
    model_class = Category
    create_form = CategoryCreateForm
    update_form = CategoryUpdateForm
    create_schema = CategoryCreateRequest
    update_schema = CategoryUpdateRequest

    is_view_and_updated = False
    is_updated = True
    is_view = False
    is_view_in_modal: bool = True

    async def get_columns(self) -> dict[str, GridColumn]:
        """Получение списка общих колонок"""
        return {
            "name": GridColumn(
                field="name",
                title="Наименование",
            ),
            "sku_prefix": GridColumn(
                field="sku_prefix",
                title="Префикс артикула",
            ),
            "toy_max_index": GridColumn(
                field="toy_max_index",
                title="Максимальный индекс игрушки",
            ),
        }

    def get_grid_column_keys(self) -> list[str]:
        """Получение списка наименований колонок для списка"""
        return [
            "id",
            "state_id",
            "name",
            "sku_prefix",
            "toy_max_index",
            "updated_on",
        ]

    async def update_form_fill(self, form: CategoryUpdateForm, entity: Category):
        """Установка значений отдельных полей формы изменения объекта"""
        form.state_id.choices = await self.service.get_dictionary_items(
            model_class=ModuleState,
            field_title="title",
            as_list_of_tuples=True,
            filters=[ModuleState.hierarchy.descendant_of(Ltree(self.get_module_code()))],
        )

    @get("/list/page")
    async def list_page(
        self,
        request: Request,
        request_data: Annotated[CategoryRetrieveCollectionRequest, Query()],
    ) -> HTMLResponse:
        """Получение списка объектов"""
        return await super().list_page(request, request_data)

    @get("/list/api")
    async def list_api(
        self,
        request: Request,
        request_data: Annotated[CategoryRetrieveCollectionRequest, Query()],
    ) -> CustomJSONResponse | FileResponse:
        """Получение списка объектов"""
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
