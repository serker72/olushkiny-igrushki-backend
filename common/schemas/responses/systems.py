from pydantic import BaseModel, ByteSize, Field


class SystemInfoResponse(BaseModel):
    """Схема ответа с информацией о системе"""

    environment: str = Field(title="Наименование окружения")
    name: str = Field(description="Наименование")
    description: str = Field(description="Описание")
    version: str = Field(description="Версия")


class SystemSettingResponse(BaseModel):
    """Схема ответа с параметрами системы"""

    page_size: int = Field(title="Количество записей на странице")
    page_size_min: int = Field(title="Минимальное количество записей на странице")
    page_size_max: int = Field(title="Максимальное количество записей на странице")
    upload_file_allowed_extensions: list[str] = Field(title="Список расширений файлов, разрещенных для загрузки")
    upload_file_max_size: ByteSize = Field(title="Максимальный размер загружаемого файла")
    public_key: str = Field(title="Публичный ключ сервера")
