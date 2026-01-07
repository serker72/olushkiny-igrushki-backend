from inspect import stack

from classy_fastapi import Routable, get
from fastapi import Request

from app_backend.routers.base import BaseRouter
from common.exceptions import get_responses
from common.schemas.responses import SystemInfoResponse, SystemSettingResponse


class SystemRouter(BaseRouter, Routable):
    """Класс представления для системы"""

    prefix = "/systems"
    tags = ["Система"]
    not_cached_endpoints = ["/info"]
    without_database_endpoints = ["/info"]
    is_security_dependency = False
    security_dependency_endpoints = ["/setting"]

    @get(
        "/info",
        summary="Информация о приложении",
        response_model=SystemInfoResponse,
        responses=get_responses(),
    )
    async def info(self, request: Request) -> SystemInfoResponse:
        """Получение информации о системе"""
        return await self.get_service(stack()[0].function, request).get_system_info()

    @get(
        "/setting",
        summary="Список параметров приложения",
        response_model=SystemSettingResponse,
        responses=get_responses(),
    )
    async def setting(self, request: Request) -> SystemSettingResponse:
        """Получение списка параметров приложения"""
        return await self.get_service(stack()[0].function, request).get_system_setting()
