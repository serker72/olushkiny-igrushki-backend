from inspect import stack
from typing import Annotated
from uuid import UUID

import aiofiles
import aiofiles.tempfile
from classy_fastapi import Routable, post
from fastapi import File as FFile
from fastapi import Form, Request, UploadFile, status

from app_backend.routers.base import BaseRouter
from app_backend.services.files import FileService
from common.exceptions import get_responses
from common.helpers import constants as c
from common.helpers.file import get_file_content_mime_type
from common.helpers.string import name_plural_to_singular
from common.schemas.requests import FileUploadRequest
from common.schemas.responses import FileRetrieveResponse


class FileRouter(BaseRouter, Routable):
    """Класс представления для файлов"""

    prefix = "/files"
    tags = ["Файлы"]

    @post(
        "/upload",
        summary="Загрузка файла для объекта",
        response_model=FileRetrieveResponse,
        responses=get_responses([status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]),
    )
    async def upload(
        self,
        request: Request,
        file: Annotated[UploadFile, FFile()],
        module_code: Annotated[str, Form()],
        entity_field: Annotated[str, Form()],
        name: Annotated[str, Form()],
        entity_field_index: Annotated[int | None, Form()] = None,
        entity_id: Annotated[int | None, Form()] = None,
        entity_uuid: Annotated[UUID | None, Form()] = None,
        tmp_entity_uuid: Annotated[UUID | None, Form()] = None,
    ) -> FileRetrieveResponse:
        """Загрузка файла для объекта"""
        async with aiofiles.tempfile.NamedTemporaryFile("wb+") as out_file:
            while chunk := await file.read(1024 * 1024):
                await out_file.write(chunk)
            await out_file.seek(0)
            content = await out_file.read()

        data = FileUploadRequest(
            module_code=module_code,
            entity_id=entity_id,
            entity_uuid=entity_uuid,
            tmp_entity_uuid=tmp_entity_uuid,
            entity_field=entity_field,
            entity_field_index=entity_field_index,
            name=name,
            size=len(content),
            content=content,
            mime_type=get_file_content_mime_type(content),
        )

        service: FileService = self.get_service(
            stack()[0].function, request, f"{name_plural_to_singular(module_code)}_{c.MODULE_CODE_FILES}"
        )
        result = await service.upload(data)
        return FileRetrieveResponse(item=result)
