from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from common.exceptions import UnprocessableEntityException
from common.helpers.file import get_file_content_mime_type


class FileCommonRequest(BaseModel):
    """Схема запроса для файла"""

    module_code: str = Field(description="Код модуля")
    entity_id: int | None = Field(None, description="ID объекта")
    entity_uuid: UUID | None = Field(None, description="UUID объекта")
    tmp_entity_uuid: UUID | None = Field(None, description="Временный UUID объекта")
    entity_field: str = Field(description="Поле объекта")

    @model_validator(mode="after")
    def validate_entity(self) -> "FileCommonRequest":
        if sum([self.entity_id is not None, self.entity_uuid is not None, self.tmp_entity_uuid is not None]) != 1:
            raise UnprocessableEntityException(code="upload_file_entity_ids_required")

        return self


class FileUploadRequest(FileCommonRequest):
    """Схема запроса загрузки файла для объекта"""

    name: str = Field(description="Имя файла")
    size: int = Field(description="Размер файла")
    content: bytes = Field(description="Содержимое файла")
    mime_type: str | None = Field(None, description="MIME-тип файла")
    entity_field_index: int | None = Field(None, description="Индекс поля объекта")

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def pre_root(self) -> "FileUploadRequest":
        if not self.mime_type:
            self.mime_type = get_file_content_mime_type(self.content)

        return self


class FileDeleteRequest(BaseModel):
    """Схема запроса на удаление файла для объекта"""

    id: UUID = Field(description="ID файла")

    model_config = ConfigDict(extra="allow")


class FileDeleteMultipleRequest(FileCommonRequest):
    delete_ids: list[UUID] | None = Field(None, description="Список идентификаторов удаляемых файлов")
    not_delete_ids: list[UUID] | None = Field(None, description="Список идентификаторов не удаляемых файлов")

    model_config = ConfigDict(extra="allow")
