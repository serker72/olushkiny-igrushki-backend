from inspect import stack

from classy_fastapi import Routable, get
from fastapi import Request
from fastapi.responses import HTMLResponse

from app_backend.routers.base import BaseUIRouter
from common.helpers import constants as c


class DashboardUIRouter(BaseUIRouter, Routable):
    """Класс представления UI для главной страницы"""

    prefix = "/lk"
    tags = ["Кабинет пользователя"]
    is_security_dependency = True

    @property
    def template_aliases(self) -> dict:
        """Словарь соответствия алиасов и имен файлов шаблонов"""
        return {
            "dashboard": "page/dashboard.html",
        }

    # async def get_template_additional_context(self, request: Request, action: str) -> dict:
    #     """Получение словаря дополнительных данных для указанного шаблона страницы"""
    #     user_service = self.get_service(stack()[0].function, request, c.MODULE_CODE_USERS)
    #     user = await user_service.get_entity(user_service.model_class, request.state.user_id)
    #     return {
    #         "user": await user.as_dict(1),
    #     }

    @get("/dashboard")
    async def dashboard(self, request: Request) -> HTMLResponse:
        """Получение страницы авторизации пользователя"""
        return await self.build_template_response(request, "dashboard", {})
