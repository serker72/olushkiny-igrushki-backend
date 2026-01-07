from uuid import UUID

from pydantic import Field

from .base import AuditModel
from .modules import ModuleShortModel


class FileModel(AuditModel):
    """Схема данных файла"""

    id: UUID = Field(description="ID файла")
    module_id: int = Field(description="ID модуля")
    entity_id: int | None = Field(description="ID объекта")
    entity_uuid: UUID | None = Field(description="UUID объекта")
    tmp_entity_uuid: UUID | None = Field(None, description="Временный UUID объекта")
    entity_field: str = Field(description="Поле объекта")
    entity_field_index: int | None = Field(description="Индекс поля объекта")
    name: str = Field(description="Имя файла")
    size: int = Field(description="Размер файла")
    mime_type: str = Field(description="MIME-тип файла")
    url: str = Field(description="Ссылка для получения файла")
    image_width: int | None = Field(default=None, description="Ширина изображения")
    image_height: int | None = Field(default=None, description="Высота изображения")

    module: ModuleShortModel = Field(description="Данные модуля")

    # @model_validator(mode="after")
    # def pre_root(self) -> "FileModel":
    #     if not self.url.startswith(
    #         f"{'https' if settings.minio_secure else 'http'}://{settings.s3_endpoint}/{settings.s3_bucket}"
    #     ):
    #         self.url = (
    #             f"{'https' if settings.s3_secure else 'http'}://{settings.s3_endpoint}/{settings.s3_bucket}{self.url}"
    #         )
    #     elif not settings.api_media_s3_usage and not self.url.startswith(settings.api_base_url):
    #         self.url = f"{settings.api_base_url}{self.url}"
    #
    #     return self
