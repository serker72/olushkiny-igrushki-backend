from pydantic import BaseModel, Field

from common.schemas.models import FileModel


class FileRetrieveResponse(BaseModel):
    """Схема ответа с данными загруженного файла"""

    item: FileModel = Field(description="Данные загруженного файла")
