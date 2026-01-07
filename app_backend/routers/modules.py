from inspect import stack
from typing import Annotated

from classy_fastapi import Routable, get
from fastapi import Query, Request, status

from app_backend.routers.base import BaseRouter
from common.exceptions import get_responses
from common.schemas.requests import BaseRetrieveCollectionRequest
from common.schemas.responses import ModuleRetrieveCollectionResponse, ModuleRetrieveResponse


class ModuleRouter(BaseRouter, Routable):
    """Класс представления для модулей"""

    prefix = "/modules"
    tags = ["Модули"]

    @get(
        "/states",
        summary="Информация о модулях",
        responses=get_responses(),
    )
    async def states(self, request: Request) -> dict:
        """Получение информации о модулях"""
        return await self.get_service(stack()[0].function, request).get_module_states("users")

    @get(
        "/",
        summary="Список модулей",
        response_model=ModuleRetrieveCollectionResponse,
        responses=get_responses(),
    )
    async def retrieve_collection(
        self,
        request: Request,
        # request_data: BaseRetrieveCollectionRequest = Depends(BaseRetrieveCollectionRequest),
        request_data: Annotated[BaseRetrieveCollectionRequest, Query()],
    ):
        """Получение списка модулей"""
        return await self.get_service(stack()[0].function, request).retrieve_collection(request_data)

    @get(
        "/{entity_id}/",
        summary="Данные модуля",
        response_model=ModuleRetrieveResponse,
        responses=get_responses([status.HTTP_404_NOT_FOUND]),
    )
    async def retrieve(
        self,
        entity_id: int,
        request: Request,
    ) -> ModuleRetrieveResponse:
        """Получение данных модуля"""
        return await self.get_service(stack()[0].function, request).retrieve(entity_id)
