from datetime import timedelta
from os.path import join

from app_backend.services.base import BaseService
from common.helpers import constants as c
from common.helpers.cryptography import get_public_key_base64
from common.helpers.dict import get_dict_from_toml_file
from common.helpers.redis_async import get_async_redis
from common.schemas.models.settings import BASE_PATH, settings
from common.schemas.responses import SystemInfoResponse, SystemSettingResponse


class SystemService(BaseService):
    """Класс сервиса для системы"""

    async def get_system_info(self) -> SystemInfoResponse:
        """Получение информации о приложении"""
        redis_connection = await get_async_redis()
        data = await redis_connection.hgetall(c.REDIS_KEY_SYSTEM_INFO)

        if not data:
            data = get_dict_from_toml_file(
                join(BASE_PATH, "pyproject.toml"),
                {"project.name": "name", "project.description": "description", "project.version": "version"},
            )
            await redis_connection.hsetex(c.REDIS_KEY_SYSTEM_INFO, mapping=data, ex=timedelta(hours=1))

        data["environment"] = settings.backend_server_name

        return SystemInfoResponse(**data)

    async def get_system_setting(self) -> SystemSettingResponse:
        """Получение списка параметров приложения"""
        return SystemSettingResponse(
            page_size=settings.backend_page_size,
            page_size_min=settings.backend_min_page_size,
            page_size_max=settings.backend_max_page_size,
            upload_file_allowed_extensions=settings.backend_upload_file_allowed_extensions,
            upload_file_max_size=settings.backend_upload_file_max_size,
            public_key=get_public_key_base64(f"{settings.backend_key_pair_path}/public_key.pem"),
        )
