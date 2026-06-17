import base64
import sys
from contextlib import suppress
from dataclasses import dataclass, field
from io import BytesIO
from mimetypes import guess_file_type
from os.path import splitext
from typing import Callable, Type
from uuid import uuid4

from cairosvg import svg2png
from loguru import logger
from miniopy_async import Minio
from miniopy_async.error import MinioException
from PIL import Image
from sqlalchemy import BigInteger, Integer, func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.elements import BinaryExpression

from app_backend.services.base import BaseModelService
from common.exceptions import ConflictException, ForbiddenException, UnprocessableEntityException
from common.helpers import constants as c
from common.helpers import timeutil
from common.helpers.exception import get_traceback
from common.helpers.file import check_file_mime_type_is_image
from common.helpers.function import execute_function
from common.helpers.string import get_file_name_from_url
from common.models import Base, File, Module
from common.schemas.models import FileModel
from common.schemas.requests import FileDeleteRequest, FileUploadRequest


@dataclass
class EntityFieldAccessControl:
    """Класс контроля доступа к полю объекта"""

    action_code: str = None
    mime_type_validator: Callable = None
    is_owner: bool = True
    state_codes: list[str] = field(default_factory=list)
    mime_types: list[str] = field(default_factory=list)


class FileService(BaseModelService):
    """Сервис для работы с файлами"""

    model_class = File

    is_upload_temporary: bool = False
    field_owner_id: str = "user_id"
    entity_fields: dict[str, EntityFieldAccessControl] = None

    _minio_client: Minio = None

    @property
    def minio_client(self) -> Minio:
        """Получение экземпляра клиента Object Storage"""
        if self._minio_client is None:
            self._minio_client = Minio(
                endpoint=f"{self.settings.minio_host}:{self.settings.minio_port}",
                access_key=self.settings.minio_access_key,
                secret_key=self.settings.minio_secret_key,
                secure=self.settings.minio_secure,
            )
            if self.settings.debug:
                self._minio_client.trace_on(sys.stderr)

        return self._minio_client

    async def check_data(
        self, data: FileUploadRequest | FileDeleteRequest
    ) -> tuple[str, Module, Type[Base], Base | None, bool, bool, bool]:
        """Проверка данных и возвращение подготовленных объектов"""
        if len(data.content) > self.settings.backend_upload_file_max_size:
            raise ConflictException(
                code="upload_file_size_is_big",
                message_context={"size": self.settings.backend_upload_file_max_size.human_readable()},
            )

        file_extension = splitext(data.name)[1].lstrip(".").lower()
        if not file_extension:
            raise ConflictException(code="upload_file_extension_not_exists")
        elif file_extension not in self.settings.backend_upload_file_allowed_extensions:
            raise ConflictException(
                code="upload_file_extension_not_allowed", message_context={"extension": file_extension}
            )

        mime_type, encoding = guess_file_type(data.name)
        logger.debug(f"data.mime_type: {data.mime_type}")
        logger.debug(f"mime_type: {mime_type}")
        logger.debug(f"encoding: {encoding}")
        if mime_type != data.mime_type:
            raise ConflictException(
                code="upload_file_extension_mime_type_not_equal_content_mime_type",
                message_context={"m1": mime_type, "m2": data.mime_type},
            )

        module: Module = await self.get_entity(Module, data.module_code, "code", "code")
        entity_model = self.get_model_class(data.module_code)
        is_id_integer = isinstance(entity_model.id.type, (BigInteger, Integer))
        is_id_uuid = isinstance(entity_model.id.type, postgresql.UUID)
        is_id_temporary = bool(data.tmp_entity_uuid)

        if is_id_integer and not data.entity_id:
            raise UnprocessableEntityException(
                code="upload_file_entity_id_required", message_context={"field": "entity_id"}
            )
        elif is_id_uuid and not data.entity_uuid:
            raise UnprocessableEntityException(
                code="upload_file_entity_id_required", message_context={"field": "entity_uuid"}
            )
        elif is_id_temporary and not self.is_upload_temporary:
            raise UnprocessableEntityException(
                code="entity_not_supported_mode_temporary_upload_file",
                message_context={"title": entity_model.case.nominative},
            )

        entity: Base | None = (
            await self.get_entity(entity_model, data.entity_id if is_id_integer else data.entity_uuid)
            if not is_id_temporary
            else None
        )

        if (
            data.entity_field not in entity_model.media_fields
            and data.entity_field not in entity_model.multiple_media_fields
        ):
            raise ConflictException(
                code="upload_file_entity_field_is_incorrect", message_context={"entity_field": data.entity_field}
            )

        if data.entity_field_index is not None and data.entity_field not in entity_model.multiple_media_fields:
            raise ConflictException(
                code="upload_file_entity_field_index_not_supported",
                message_context={"entity_field": data.entity_field, "title": entity.case.nominative},
            )

        if not isinstance(self.entity_fields, dict) or data.entity_field not in self.entity_fields.keys():
            raise ConflictException(
                code="upload_file_entity_field_acl_is_not_found", message_context={"entity_field": data.entity_field}
            )

        entity_field_acl: EntityFieldAccessControl = self.entity_fields[data.entity_field]

        # Проверка владельца объекта
        if entity_field_acl.is_owner and getattr(entity, self.field_owner_id) != self.user_id:
            raise ForbiddenException(
                code="cannot_upload_file_for_another_user_object",
                message_context={"field": data.entity_field, "title": entity.case.nominative, "id": entity.id},
            )

        # Проверка статуса объекта
        if (
            len(entity_field_acl.state_codes) > 0
            and self.get_model_state_column(entity_model) is not None
            and entity.state.code not in entity_field_acl.state_codes
        ):
            raise ForbiddenException(
                code="upload_file_entity_state_not_allowed",
                message_context={
                    "field": data.entity_field,
                    "title": entity.case.nominative,
                    "state": entity.state.title,
                },
            )

        # Проверка mime_type файла по списку разрешенных
        if len(entity_field_acl.mime_types) > 0 and data.mime_type not in entity_field_acl.mime_types:
            raise ForbiddenException(
                code="upload_file_mime_type_not_allowed",
                message_context={
                    "field": data.entity_field,
                    "title": entity.case.nominative,
                    "mime_type": data.mime_type,
                },
            )

        # Проверка mime_type файла с помощью функции валидатора
        if callable(entity_field_acl.mime_type_validator) and not await execute_function(
            entity_field_acl.mime_type_validator, data.mime_type
        ):
            raise ForbiddenException(
                code="upload_file_mime_type_not_allowed",
                message_context={
                    "field": data.entity_field,
                    "title": entity.case.nominative,
                    "mime_type": data.mime_type,
                },
            )

        return file_extension, module, entity_model, entity, is_id_integer, is_id_uuid, is_id_temporary

    def get_entity_file_filters(
        self, data: FileUploadRequest | FileDeleteRequest, is_id_integer: bool, module: Module, entity: Base | None
    ) -> list[BinaryExpression]:
        """Построение списка фильтров для получения файла без учета индекса"""
        filters = [File.module_id == module.id, File.entity_field == data.entity_field]
        if data.tmp_entity_uuid:
            filters.extend(
                [
                    File.tmp_entity_uuid == data.tmp_entity_uuid,
                    File.entity_id.is_(None),
                    File.entity_uuid.is_(None),
                ]
            )
        else:
            filters.append((File.entity_id if is_id_integer else File.entity_uuid) == entity.id)

        return filters

    def get_entity_file_field_index_filters(
        self, data: FileUploadRequest | FileDeleteRequest, is_id_integer: bool, module: Module, entity: Base | None
    ) -> list[BinaryExpression]:
        """Построение списка фильтров для получения файла с учетом индекса"""
        filters = self.get_entity_file_filters(data, is_id_integer, module, entity)
        if data.entity_field_index is not None:
            filters.append(File.entity_field_index == data.entity_field_index)
        else:
            filters.append(File.entity_field_index.is_(None))

        return filters

    async def get_bucket_name(self, data: FileUploadRequest) -> tuple[str, bool]:
        """Получение имени корзины"""
        is_image = check_file_mime_type_is_image(data.mime_type)
        bucket_name = self.settings.minio_images_bucket_name if is_image else self.settings.minio_files_bucket_name

        logger.info(f"is_image: {is_image}")
        logger.info(f"bucket_name: {bucket_name}")

        if not await self.minio_client.bucket_exists(bucket_name):
            await self.minio_client.make_bucket(bucket_name)

        if is_image and not await self.minio_client.bucket_exists(self.settings.minio_images_cache_bucket_name):
            await self.minio_client.make_bucket(self.settings.minio_images_cache_bucket_name)

        return bucket_name, is_image

    async def upload(self, data: FileUploadRequest) -> FileModel:
        """Загрузка файла для указанного поля объекта"""
        (
            file_extension,
            module,
            entity_model,
            entity,
            is_id_integer,
            is_id_uuid,
            is_id_temporary,
        ) = await self.check_data(data)

        if data.entity_field in entity_model.multiple_media_fields:
            base_filters = self.get_entity_file_filters(data, is_id_integer, module, entity)
            statement = select(func.max(File.entity_field_index)).filter(*base_filters)
            statement_result = await self.session.execute(statement)
            max_index = statement_result.scalar()
            data.entity_field_index = 0 if max_index is None else max_index + 1
        else:
            data.entity_field_index = None

        bucket_name, is_image = await self.get_bucket_name(data)

        if is_image:
            with Image.open(BytesIO(svg2png(data.content) if file_extension == "svg" else data.content)) as img:
                image_width, image_height = img.size
        else:
            image_width = None
            image_height = None

        filters = self.get_entity_file_field_index_filters(data, is_id_integer, module, entity)
        statement = select(File).filter(*filters)
        statement_result = await self.session.execute(statement)
        entity_file: File | None = statement_result.scalar()

        """
        Для исключения необходимости добавления GET параметра `t={timestamp}` к ссылке получения файла, 
        каждый загруженный файл сохраняется с новым UUID в имени, а существующий файл предварительно удаляется. 
        """
        if entity_file is not None:
            with suppress(MinioException):
                await self.minio_client.remove_object(
                    bucket_name=bucket_name,
                    object_name=f"{data.module_code}/{get_file_name_from_url(entity_file.url)}",
                )

        file_id = uuid4()
        file_name = f"{file_id}.{file_extension}"

        try:
            await self.minio_client.put_object(
                bucket_name=bucket_name,
                object_name=f"{data.module_code}/{file_name}",
                data=BytesIO(data.content),
                length=data.size,
                content_type=data.mime_type,
                metadata={"original_file_name": base64.urlsafe_b64encode(data.name.encode("utf-8")).decode("utf-8")},
            )
        except Exception as e:
            trace = get_traceback(e)
            logger.error(trace)
            raise ConflictException(code="upload_file_write_error", message_context={"name": file_name, "error": e})

        dt_current = timeutil.utcnow()

        if entity_file is None:
            entity_file = File(
                id=file_id,
                module_id=module.id,
                entity_id=data.entity_id,
                entity_uuid=data.entity_uuid,
                tmp_entity_uuid=data.tmp_entity_uuid,
                entity_field=data.entity_field,
                entity_field_index=data.entity_field_index,
                name=data.name,
                size=data.size,
                mime_type=data.mime_type,
                url=f"/{module.code}/{file_id}.{file_extension}",
                image_width=image_width,
                image_height=image_height,
                created_by=self.user_id,
                updated_by=self.user_id,
                created_on=dt_current,
                updated_on=dt_current,
            )
            self.session.add(entity_file)
        else:
            entity_file.name = data.name
            entity_file.size = data.size
            entity_file.mime_type = data.mime_type
            entity_file.updated_by = self.user_id
            entity_file.updated_on = dt_current
            entity_file.url = f"/{module.code}/{file_id}.{file_extension}"
            entity_file.image_width = image_width
            entity_file.image_height = image_height

        try:
            await self.commit_and_refresh_entity(entity_file)
        except Exception as e:
            trace = get_traceback(e)
            logger.error(trace)

            with suppress(MinioException):
                await self.minio_client.remove_object(
                    bucket_name=bucket_name,
                    object_name=f"{data.module_code}/{file_name}",
                )

            raise ConflictException(
                code="upload_file_model_save_error", message_context={"name": data.name, "error": e}
            )

        return await self.entity_to_schema(entity_file)


class UserFileService(FileService, BaseModelService):
    """Сервис для работы с файлами пользователя"""

    field_owner_id = "id"
    entity_fields = {
        "photo": EntityFieldAccessControl(
            state_codes=[c.STATE_APPROVED],
            mime_type_validator=check_file_mime_type_is_image,
        )
    }
