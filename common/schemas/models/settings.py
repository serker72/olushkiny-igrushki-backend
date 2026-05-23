import os
from datetime import timedelta
from typing import Any

from loguru import logger
from pydantic import BaseModel, ByteSize, ConfigDict, EmailStr, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from common.helpers.dict import maybe_dict_from_file
from common.helpers.file import check_directory_exists, check_directory_writable, check_file_exists, get_file_content
from common.helpers.string import CustomListOfStrings


class QueueWorkerParam(BaseModel):
    """Схема данных обработчика очереди RabbitMQ"""

    class_name: str = Field(description="Имя класса обработчика очереди")
    reconnect_timeout: int = Field(
        2, description="Таймаут в секундах между попытками повторного подключения обработчика к RabbitMQ"
    )
    consume_method_is_lock: bool = Field(
        False, description="Флаг создания блокировки запуска метода обработки сообщения из очереди"
    )
    consume_method_lock_ttl: int = Field(
        60, description="Время жизни блокировки запуска метода обработки сообщения из очереди"
    )
    consume_method_lock_is_delete: bool = Field(
        False, description="Флаг удаления блокировки запуска метода обработки сообщения из очереди"
    )


class QueueParam(BaseModel):
    """Схема данных очереди RabbitMQ"""

    queue_name: str = Field(description="Имя очереди RabbitMQ")
    message_delay_time: int = Field(0, description="Время задержки сообщений в секундах")
    worker_count: int = Field(1, description="Количество обработчиков очереди")
    worker_param: QueueWorkerParam = Field(description="Параметры обработчика очереди")


class BackendSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    # rabbitmq
    rabbitmq_username: str = Field("guest")
    rabbitmq_password: str = Field("guest")
    rabbitmq_host: str = Field("localhost")
    rabbitmq_port: int = Field(5672)
    rabbitmq_vhost: str = Field("/")

    # redis
    redis_username: str = Field("default")
    redis_password: str = Field("")
    redis_host: str = Field("localhost")
    redis_port: int = Field(6379)
    redis_db: int = Field(0)

    # postgres
    postgres_host: str = Field("localhost")
    postgres_port: int = Field(5432)
    postgres_db: str = Field("olushkiny_igrushki")
    postgres_user: str = Field("olushkiny_igrushki")
    postgres_password: str = Field("olushkiny_igrushki")
    postgres_test_db: str = Field("olushkiny_igrushki_test")
    postgres_test_user: str = Field("olushkiny_igrushki_test")
    postgres_test_password: str = Field("olushkiny_igrushki")

    # minio
    minio_host: str = Field("localhost")
    minio_port: int = Field(9000)
    minio_access_key: str = Field("")
    minio_secret_key: str = Field("")
    minio_secure: bool = Field(True)
    minio_images_bucket_name: str = Field("images", description="Имя корзины для изображений")
    minio_files_bucket_name: str = Field("files", description="Имя корзины для файлов")
    minio_images_cache_bucket_name: str = Field("images-cache", description="Имя корзины для кеша изображений")

    # jwt
    authjwt_algorithm: str = Field("RS512", description="Алгоритм подписи JWT")
    authjwt_access_token_expires: int = Field(3600, description="Срок действия access токена в секундах")
    authjwt_refresh_token_expires: int = Field(86400, description="Срок действия refresh токена в секундах")
    # authjwt_token_location: list[str] = Field(["cookies", "headers"], description="Местоположение токена JWT")
    authjwt_token_location: list[str] = Field(["cookies"], description="Местоположение токена JWT")
    authjwt_cookie_csrf_protect: bool = Field(True, description="Флаг использования CSRF токена для защиты cookies")
    authjwt_cookie_domain: str | None = Field(None, description="Домен cookies")
    authjwt_cookie_secure: bool = Field(True, description="Флаг использования HTTPS протокола для передачи cookies")
    authjwt_access_cookie_key: str = Field("olushkiny_igrushki_access_token", description="Имя cookie для access_token")
    authjwt_refresh_cookie_key: str = Field(
        "olushkiny_igrushki_refresh_token", description="Имя cookie для refresh_token"
    )

    # smtp
    smtp_host: str = Field(None)
    smtp_starttls: bool = Field(None)
    smtp_ssl: bool = Field(None)
    smtp_user: str = Field(None)
    smtp_password: str = Field(None)
    smtp_port: int = Field(None)
    smtp_mail_from: str = Field(None)
    smtp_timeout: int = Field(None)
    smtp_retry_limit: int = Field(None)

    # common
    debug: bool = Field(False, description="Флаг отладки")
    task_lock_timeout: int = Field(300, description="Время блокировки задачи в секундах")

    # backend
    backend_system_name: str = Field("Олюшкины игрушки", description="Имя сервиса")
    backend_server_name: str = Field("prod", description="Имя сервера")
    backend_base_url: str = Field("http://localhost:8000", description="Основной URL")
    backend_api_prefix: str = Field("/api/v1", description="Префикс")
    backend_cors_allow_origin: str = Field("*", description="Список разрешенных доменов для CORS")
    backend_page_size: int = Field(10, description="Количество записей на странице")
    backend_min_page_size: int = Field(5, description="Минимальное количество записей на странице")
    backend_max_page_size: int = Field(100, description="Максимальное количество записей на странице")
    backend_page_sizes: list[int] = Field(
        [5, 10, 15, 20, 25, 30, 50, 100], title="Список допустимых значений количества записей на странице"
    )
    backend_password_salt: str = Field("backend_password_salt", description="Соль для генерации пароля")
    backend_password_secret_key: str = Field(
        "backend_password_secret_key", description="Секретный ключ для генерации пароля"
    )
    backend_password_characters: str = Field(
        "ascii_lowercase,ascii_uppercase,digits,punctuation",
        description="Набор символов, разрешенных для использования в пароле",
    )
    backend_password_min_length: int = Field(8, description="Минимальная длина пароля")
    backend_log_path: str = Field(description="Каталог хранения файлов с протоколами работы приложения")
    backend_upload_file_max_size: ByteSize = Field("25MiB", description="Максимальный размер загружаемого файла")
    backend_upload_file_allowed_extensions: CustomListOfStrings | None = Field(
        ["png", "jpg", "jpeg", "svg", "webp"], description="Список расширений файлов, разрещенных для загрузки"
    )
    backend_media_not_allowed_file_extensions: str = Field(
        "exe,com,bat,cmd,sh", description="Список расширений файлов, запрещенных для загрузки"
    )
    backend_media_path: str = Field(description="Каталог хранения загружаемых файлов")
    backend_static_path: str = Field(description="Каталог хранения статических файлов")
    backend_key_pair_path: str = Field(description="Каталог хранения ключей сервера")
    backend_private_key_password: str | None = Field(description="Пароль приватного ключа сервера")
    backend_csrf_protec_secret_key: str = Field(description="Секретный ключ для CSRF")
    backend_secret_key: str = Field(description="Секретный ключ для сессии")

    ##### confirmation_code #####
    backend_user_confirmation_code_length: int = Field(6, description="Количество цифр в коде подтверждения")
    backend_user_confirmation_code_lifetime: int = Field(3600, description="Время жизни кода подтверждения в секундах")
    backend_user_confirmation_code_limit_timeout: timedelta = Field(
        "P1D", description="Длительность периода контроля количества попыток отправки кода подтверждения"
    )
    backend_user_confirmation_code_limit_same_group_attempts: int = Field(
        3, description="Количество попыток отправки кода подтверждения в пределах группы"
    )
    backend_user_confirmation_code_limit_same_group_attempts_timeout: int = Field(
        120, description="Интервал между попытками отправки кода подтверждения в пределах группы в секундах"
    )
    backend_user_confirmation_code_limit_group_count: int = Field(
        3, description="Количество групп попыток отправки кода подтверждения в пределах периода контроля"
    )
    backend_user_confirmation_code_limit_group_timeout: int = Field(
        600,
        description="Интервал между группами попыток отправки кода подтверждения в пределах периода контроля в секундах",
    )

    # queue_processing
    queue_processing_processing_timeout: int = Field(
        default=5,
        description="Приложение queue_processing: таймаут в секундах между проверками списка обрабатываемых очередей RabbitMQ",
    )
    queue_processing_file_name_with_queues: str = Field(
        default=".queues.json",
        description="Приложение queue_processing: имя файла со списком обрабатываемых очередей RabbitMQ",
    )
    queue_processing_queues: dict[str, QueueParam] | None = Field(
        default=None,
        description="Приложение queue_processing: список обрабатываемых очередей RabbitMQ",
    )
    queue_processing_python_interpreter: str = Field(
        default="/usr/local/bin/python", description="Приложение queue_processing: интерпретатор Python"
    )

    # sqlalchemy
    sa_debug: bool = Field(False)
    sa_pool_size: int = Field(20)
    sa_max_overflow: int = Field(-1)
    sa_pool_timeout: float = Field(30.0)
    sa_pool_recycle: int = Field(3600)
    sa_pool_use_lifo: bool = Field(True)
    sa_pool_pre_ping: bool = Field(True)

    # thumbor
    thumbor_base_url: str = Field("http://localhost/media", description="URL сервера Thumbor")
    thumbor_security_key: str = Field(description="Секретный ключ сервера Thumbor")

    thumbor_image_params: dict[str, dict] = {
        "w200_h200": {
            "width": 200,
            "height": 200,
            # "filters": ["no_upscale()", "quality(65)"],
        },
        "w200_h200_webp": {
            "width": 200,
            "height": 200,
            # "filters": ["no_upscale()", "quality(65)", "format(webp)"],
            "filters": ["format(webp)"],
        },
        "w360_h640": {
            "width": 360,
            "height": 640,
            # "filters": ["no_upscale()", "quality(65)"],
        },
        "w360_h640_webp": {
            "width": 360,
            "height": 640,
            # "filters": ["no_upscale()", "quality(65)", "format(webp)"],
            "filters": ["format(webp)"],
        },
        "w720_h1280": {
            "width": 720,
            "height": 1280,
            # "filters": ["no_upscale()", "quality(65)"],
        },
        "w720_h1280_webp": {
            "width": 720,
            "height": 1280,
            # "filters": ["no_upscale()", "quality(65)", "format(webp)"],
            "filters": ["format(webp)"],
        },
        "w720": {
            "width": 720,
            "height": 0,
            # "filters": ["no_upscale()", "quality(65)"],
        },
        "w720_webp": {
            "width": 720,
            "height": 0,
            # "filters": ["no_upscale()", "quality(65)", "format(webp)"],
            "filters": ["format(webp)"],
        },
        "original": {
            "width": 0,
            "height": 0,
            # "filters": ["no_upscale()", "quality(65)"],
        },
        "original_webp": {
            "width": 0,
            "height": 0,
            # "filters": ["no_upscale()", "quality(65)", "format(webp)"],
            "filters": ["format(webp)"],
        },
    }

    @model_validator(mode="before")
    def check_field(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data["queue_processing_queues"] = maybe_dict_from_file(data["queue_processing_file_name_with_queues"])

        return data

    def get_redis_url(self) -> str:
        """Получение URL подключения к серверу Redis"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        else:
            return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    def get_rabbitmq_url(self) -> str:
        """Получение URL подключения к серверу RabbitMQ"""
        return (
            f"amqp://{self.rabbitmq_username}:{self.rabbitmq_password}@"
            f"{self.rabbitmq_host}:{self.rabbitmq_port}{self.rabbitmq_vhost}"
        )

    def get_postgres_url(self) -> str:
        """Получение URL подключения к рабочей БД сервера PostgreSQL с использованием psycopg2"""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def get_postgres_test_url(self) -> str:
        """Получение URL подключения к тестовой БД сервера PostgreSQL с использованием psycopg2"""
        return (
            f"postgresql+psycopg2://{self.postgres_test_user}:{self.postgres_test_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_test_db}"
        )

    def get_postgres_async_url(self) -> str:
        """Получение URL подключения к рабочей БД сервера PostgreSQL с использованием asyncpg"""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def get_postgres_async_test_url(self) -> str:
        """Получение URL подключения к тестовой БД сервера PostgreSQL с использованием asyncpg"""
        return (
            f"postgresql+asyncpg://{self.postgres_test_user}:{self.postgres_test_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_test_db}"
        )

    def get_thumbor_image_params(self, key: str = None) -> dict:
        """Получение параметров обработки изображений Thumbor"""
        return self.thumbor_image_params.get(key if key in self.thumbor_image_params.keys() else "original_webp")

    @model_validator(mode="before")
    def check_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            msg = None
            if data.get("backend_key_pair_path"):
                data["backend_key_pair_path"] = data["backend_key_pair_path"].rstrip("/")

            if data.get("backend_log_path"):
                data["backend_log_path"] = data["backend_log_path"].rstrip("/")

            if data.get("backend_media_path"):
                data["backend_media_path"] = data["backend_media_path"].rstrip("/")

            if data.get("backend_static_path"):
                data["backend_static_path"] = data["backend_static_path"].rstrip("/")

            if data.get("backend_key_pair_path"):
                data["backend_private_key_password"] = (
                    data["backend_private_key_password"]
                    and data["backend_private_key_password"].encode("utf-8")
                    or None
                )

            private_key_name = os.path.join(data["backend_key_pair_path"], "private_key.pem")
            public_key_name = os.path.join(data["backend_key_pair_path"], "public_key.pem")

            if not check_directory_exists(data["backend_key_pair_path"]):
                msg = f"Каталог '{data['backend_key_pair_path']}' не обнаружен"
            elif not check_directory_exists(data["backend_media_path"]):
                msg = f"Каталог '{data['backend_media_path']}' не обнаружен"
            elif not check_directory_exists(data["backend_log_path"]):
                msg = f"Каталог '{data['self.backend_log_path']}' не обнаружен"
            elif not check_directory_writable(data["backend_log_path"]):
                msg = f"Каталог '{data['self.backend_log_path']}' не доступен для записи"
            elif not check_directory_writable(data["backend_media_path"]):
                msg = f"Каталог '{data['backend_media_path']}' не доступен для записи"
            elif not check_file_exists(private_key_name):
                msg = f"Файл '{private_key_name}' не обнаружен"
            elif not check_file_exists(public_key_name):
                msg = f"Файл '{public_key_name}' не обнаружен"

            if msg is not None:
                logger.error(msg)
                raise ValueError(msg)

            data["authjwt_private_key"] = get_file_content(private_key_name).decode("utf-8")
            data["authjwt_public_key"] = get_file_content(public_key_name).decode("utf-8")

        return data


class AuthJWTSettings(BaseModel):
    authjwt_secret_key: str
    authjwt_access_token_expires: int = Field(3600)
    authjwt_refresh_token_expires: int = Field(86400)


class WebSocketSettingsModel(BaseModel):
    """Схема данных с параметрами приложения"""

    max_file_size: float = Field(description="Максимальный размер файла")


class TokenClaims(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fio: str
    email: EmailStr
    iss: str
    aud: str
    exp: int
    sub: str
    iat: int
    jti: str


settings = BackendSettings()
BASE_PATH = os.getcwd()
