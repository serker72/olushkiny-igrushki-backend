from uuid import UUID

from loguru import logger
from pydantic import BaseModel, Field, model_validator

from common.schemas.models import CustomIntOrNone
from common.schemas.models.settings import settings


class BaseRetrieveRequest(BaseModel):
    """Схема базового запроса получения данных объекта"""

    entity_id: int | UUID = Field(description="ID объекта")


class BaseUpdateRequest(BaseModel):
    """Схема базового запроса изменения данных объекта"""

    entity_id: int | UUID = Field(description="ID объекта")
    entity_data: BaseModel = Field(description="Данные объекта")


class BasePatchRequest(BaseModel):
    """Схема базового запроса частичного изменения данных объекта"""

    entity_id: int | UUID = Field(description="ID объекта")
    entity_data: BaseModel = Field(description="Данные объекта")


class BaseChangeStateRequest(BaseModel):
    """Схема базового запроса изменения статуса объекта"""

    entity_id: int = Field(description="ID объекта")
    state_id: int = Field(description="ID статуса")


class BaseDeleteRequest(BaseModel):
    """Схема базового запроса удаления объекта"""

    entity_id: int | UUID = Field(description="ID объекта")


class BaseRetrieveCollectionRequest(BaseModel):
    """Схема базового запроса получения списка объектов"""

    sort: str | None = Field(default=None, description="Список полей для сортировки")
    page: CustomIntOrNone = Field(default=1, description="Номер страницы")
    limit: CustomIntOrNone = Field(default=None, description="Количество объектов на странице")
    is_export: bool | None = Field(False, description="Флаг экспорта")
    image_format: str | None = Field(default=None, description="Формат изображения")
    image_width: CustomIntOrNone = Field(default=None, description="Ширина изображения")
    image_height: CustomIntOrNone = Field(default=None, description="Высота изображения")

    @model_validator(mode="after")
    def check_field(self) -> "BaseRetrieveCollectionRequest":
        """Поствалидация полей модели"""
        logger.debug(f"request_data: {repr(self.model_dump())}")
        if not self.limit:
            self.limit = settings.backend_page_size
        if not self.page:
            self.page = 1
        if self.limit and self.limit < settings.backend_min_page_size:
            self.limit = settings.backend_min_page_size
        if self.limit and self.limit > settings.backend_max_page_size:
            self.limit = settings.backend_max_page_size

        logger.debug(f"request_data: {repr(self.model_dump())}")
        return self
