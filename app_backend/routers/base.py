from classy_fastapi import Routable
from fastapi import Request
from loguru import logger

# from common.helpers.string import name_plural_to_singular
from app_backend.services.base import BaseServiceType, ServiceManager
from common.helpers.database import get_request_sa_session


class BaseRouter(Routable):
    """Класс базового представления"""

    prefix: str = None
    tags: list[str] = None
    service_manager: ServiceManager = None
    not_cached_endpoints: list[str] = None
    without_database_endpoints: list[str] = None
    is_security_dependency: bool = True
    security_dependency_endpoints: list[str] = None

    def __init__(self, service_manager: ServiceManager, **kwargs) -> None:
        """Конструктор класса"""
        self.service_manager = service_manager
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
