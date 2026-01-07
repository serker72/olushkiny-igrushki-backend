from inspect import stack
from typing import Annotated

from classy_fastapi import Routable, get, put
from fastapi import Query, Request, status
from loguru import logger

from app_backend.routers.base import BaseRouter
from common.exceptions import get_responses
from common.schemas.models import ImageParamSchema
from common.schemas.requests import BaseRetrieveCollectionRequest, UserUpdateProfileRequest
from common.schemas.responses import UserRetrieveCollectionPaginateResponse, UserRetrieveResponse


class UserRouter(BaseRouter, Routable):
    """Класс представления для пользователей"""

    prefix = "/users"
    tags = ["Пользователи"]

    @get(
        "/me",
        summary="Данные текущего пользователя",
        response_model=UserRetrieveResponse,
        responses=get_responses([status.HTTP_401_UNAUTHORIZED]),
    )
    async def retrieve_current_user(
        self,
        request: Request,
        image_params: Annotated[ImageParamSchema, Query()],
    ) -> UserRetrieveResponse:
        """Получение данных текущего пользователя"""
        logger.debug(f"image_params: {repr(image_params.model_dump())}")
        return await self.get_service(stack()[0].function, request).retrieve(request.state.user_id, image_params)

    @put(
        "/me",
        summary="Изменение данных текущего пользователя",
        response_model=UserRetrieveResponse,
        responses=get_responses([status.HTTP_401_UNAUTHORIZED]),
    )
    async def update_current_user(
        self,
        request: Request,
        # request_data: UserUpdateProfileRequest = Depends(UserUpdateProfileRequest),
        request_data: UserUpdateProfileRequest,
    ) -> UserRetrieveResponse:
        """Изменение данных текущего пользователя"""
        return await self.get_service(stack()[0].function, request).update(
            request.state.user_id, request_data, is_return_response_schema=True
        )

    @get(
        "/",
        summary="Список пользователей",
        response_model=UserRetrieveCollectionPaginateResponse,
        responses=get_responses(),
    )
    async def retrieve_collection(
        self,
        request: Request,
        # request_data: BaseRetrieveCollectionRequest = Depends(BaseRetrieveCollectionRequest),
        request_data: Annotated[BaseRetrieveCollectionRequest, Query()],
    ):
        """Получение списка пользователей"""
        logger.debug(f"request_data: {repr(request_data.model_dump())}")
        return await self.get_service(stack()[0].function, request).retrieve_collection(request_data)

    @get(
        "/{entity_id:int}",
        summary="Данные указанного пользователя",
        response_model=UserRetrieveResponse,
        responses=get_responses([status.HTTP_404_NOT_FOUND]),
    )
    async def retrieve(
        self,
        entity_id: int,
        request: Request,
    ) -> UserRetrieveResponse:
        """Получение данных указанного пользователя"""
        return await self.get_service(stack()[0].function, request).retrieve(entity_id)
