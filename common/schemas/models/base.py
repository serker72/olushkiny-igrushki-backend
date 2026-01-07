from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, ClassVar, TypeVar

import pytz
from libthumbor import CryptoURL
from pydantic import (
    BaseModel,
    BeforeValidator,
    EmailStr,
    Field,
    PlainSerializer,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    model_validator,
)
from pydantic.functional_validators import WrapValidator

from common.exceptions import UnprocessableEntityException
from common.helpers import constants as c
from common.helpers.dict import maybe_dict, maybe_dict_from_file
from common.helpers.password import get_password_hash, is_password_hash, validate_password
from common.helpers.phone import verify_user_phone
from common.schemas.models.settings import settings


def maybe_bool(v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> bool:
    if isinstance(v, str):
        return v.lower() in ("yes", "true", "t", "1")
    elif isinstance(v, int):
        return v == 1

    return v


def maybe_bool_or_none(v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> bool | None:
    if isinstance(v, str):
        return v.lower() in ("yes", "true", "t", "1") if v else None
    elif isinstance(v, int):
        return v == 1

    return v


def maybe_datetime(v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> datetime:
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v)
        except (TypeError, ValueError):
            try:
                return datetime.strptime(v, c.FORMAT_DATE_TIME).replace(tzinfo=pytz.utc)
            except (TypeError, ValueError):
                raise UnprocessableEntityException(code="invalid_request_data_format")

    return v


def maybe_datetime_or_none(v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> datetime | None:
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v)
        except (TypeError, ValueError):
            return None

    return v


def maybe_date_or_none(v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> date | None:
    if isinstance(v, str):
        try:
            return date.fromisoformat(v)
        except (ValueError, TypeError):
            return None

    return v


def maybe_int_or_none(v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> int | None:
    if isinstance(v, str):
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    return v


def get_thumbor_image_url(
    file_name: str,
    thumbor_param_key: str = None,
    image_params: ImageParamSchema = None,
    image_width: int = None,
    image_height: int = None,
) -> str:
    """Получение ссылки на изображение после обработки Thumbor"""
    thumbor_params = settings.get_thumbor_image_params(thumbor_param_key)
    file_name_parts = file_name.split("?")
    thumbor_params["image_url"] = file_name_parts[0].lstrip("/")

    if image_params and image_params.image_format:
        thumbor_params["filters"] = [
            f"format({image_params.image_format})" if f.startswith("format(") else f for f in thumbor_params["filters"]
        ]

    if image_width and image_height:
        is_vertical = (image_width // image_height) < 1
        if is_vertical:
            thumbor_params["width"] = 0
            thumbor_params["height"] = image_params and image_params.image_height or thumbor_params["height"]
        else:
            thumbor_params["width"] = image_params and image_params.image_width or thumbor_params["width"]
            thumbor_params["height"] = 0
    elif image_params and image_params.image_width and image_params.image_height:
        thumbor_params["width"] = image_params.image_width
        thumbor_params["height"] = image_params.image_height

    return f"{settings.thumbor_base_url.rstrip('/')}{thumbor_crypto.generate(**thumbor_params)}"


thumbor_crypto = CryptoURL(key=settings.thumbor_security_key)
CustomBool = Annotated[bool, WrapValidator(maybe_bool)]
CustomBoolOrNone = Annotated[bool, WrapValidator(maybe_bool_or_none)]
CustomDatetime = Annotated[datetime, WrapValidator(maybe_datetime)]
CustomDatetimeOrNone = Annotated[datetime, WrapValidator(maybe_datetime_or_none)]
CustomDateOrNone = Annotated[datetime, WrapValidator(maybe_date_or_none)]
CustomDict = Annotated[dict, WrapValidator(maybe_dict)]
CustomDictFromFile = Annotated[dict, BeforeValidator(maybe_dict_from_file)]
CustomDecimal = Annotated[Decimal, PlainSerializer(lambda x: float(x), return_type=float)]
CustomIntOrNone = Annotated[int, WrapValidator(maybe_int_or_none)]


class AuditModel(BaseModel):
    """Схема данных пользователя"""

    created_by: int = Field(description="ID создателя")
    created_on: datetime = Field(description="Время создания")
    updated_by: int = Field(description="ID редактора")
    updated_on: datetime = Field(description="Время изменения")
    creator_fio: str = Field(description="ФИО создателя")
    updater_fio: str = Field(description="ФИО редактора")


class BaseFilterCollectionModel(BaseModel):
    """Схема данных фильтрации списка объектов"""

    state_id: list[int] | None = Field(default=None, description="Список ID статусов объекта")
    module_id: list[int] | None = Field(default=None, description="Список ID модулей")
    # search: str | None = Field(default=None, description="Произвольная строка поиска")


class PasswordSchema(BaseModel):
    """Схема запроса изменения пароля пользователя"""

    password: str = Field(description="Пароль", min_length=settings.backend_password_min_length)

    @model_validator(mode="before")
    def check_password(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("password") and not is_password_hash(data["password"]):
                if not validate_password(
                    data["password"], settings.api_password_characters, settings.backend_password_min_length
                ):
                    raise UnprocessableEntityException(code="user_password_not_meet_security_requirements")
                data["password"] = get_password_hash(
                    data["password"], settings.backend_password_salt, settings.backend_password_secret_key
                )
        return data


class PhoneSchema(BaseModel):
    """Схема данных номера телефона"""

    phone: str = Field(description="Номер телефона")

    @model_validator(mode="before")
    def pre_phone(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("phone"):
                data["phone"] = verify_user_phone(data["phone"])
                if data["phone"] is None:
                    raise UnprocessableEntityException(code="phone_number_invalid_format")

        return data


class EmailSchema(BaseModel):
    """Схема данных email"""

    email: EmailStr = Field(description="Адрес e-mail")

    @model_validator(mode="before")
    def pre_email(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("email"):
                data["email"] = data["email"].lower()

        return data


class EmailOptionalSchema(EmailSchema):
    """Схема опциональных данных email"""

    email: EmailStr | None = Field(default=None, description="Адрес e-mail")


class PhoneOptionalSchema(PhoneSchema):
    """Схема опциональных данных номера телефона"""

    phone: str | None = Field(default=None, description="Номер телефона")


class EmailOrPhoneSchema(EmailOptionalSchema, PhoneOptionalSchema):
    """Схема данных email или phone"""

    @model_validator(mode="before")
    def pre_login(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if len(list(filter(lambda x: x is not None, [data.get("phone"), data.get("email")]))) != 1:
                raise UnprocessableEntityException(
                    code="invalid_request_data_format_with_reason",
                    message_context={"reason": "Необходимо указать значение одного из параметров phone или email"},
                )

        return data


class EmailAndOrPhoneSchema(EmailOptionalSchema, PhoneOptionalSchema):
    """Схема данных email и/или phone"""

    @model_validator(mode="before")
    def pre_login(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if len(list(filter(lambda x: x is not None, [data.get("phone"), data.get("email")]))) < 1:
                raise UnprocessableEntityException(
                    code="invalid_request_data_format_with_reason",
                    message_context={
                        "reason": "Необходимо указать значение одного или двух параметров - phone и email"
                    },
                )

        return data


class ImageParamSchema(BaseModel):
    image_format: str | None = Field(default=None, description="Формат изображения")
    image_width: CustomIntOrNone = Field(default=None, description="Ширина изображения")
    image_height: CustomIntOrNone = Field(default=None, description="Высота изображения")

    @model_validator(mode="after")
    def validate_entity(self) -> "ImageParamSchema":
        if sum([self.image_width is not None, self.image_height is not None]) == 1:
            raise UnprocessableEntityException(code="image_params_width_and_height_required")

        return self


class ImageSchema(BaseModel):
    """Схема данных изображения"""

    view_action: ClassVar[str] = "retrieve"
    thumbor_params: ClassVar[dict] = {}
    image_params: ClassVar[ImageParamSchema | None] = None

    photo: str | None = Field(default=None, description="Ссылка для получения фото")

    @model_validator(mode="before")
    def pre_images(cls, data: Any) -> Any:
        """Обработка изображений"""
        if isinstance(data, dict):
            for field_name, param_keys in cls.thumbor_params.items():
                if data.get(field_name):
                    if isinstance(data[field_name], dict):
                        src = data[field_name].get("url")
                        image_width = data[field_name].get("image_width")
                        image_height = data[field_name].get("image_height")
                    else:
                        src = data[field_name]
                        image_width = None
                        image_height = None

                    if isinstance(src, str) and not src.startswith("http"):
                        data[field_name] = get_thumbor_image_url(
                            src,
                            param_keys.get(cls.view_action, param_keys.get("all")),
                            cls.image_params,
                            image_width,
                            image_height,
                        )

        return data


class ImagesSchema(BaseModel):
    """Схема данных изображений"""

    view_action: ClassVar[str] = "retrieve"
    thumbor_params: ClassVar[dict] = {}
    image_params: ClassVar[ImageParamSchema | None] = None

    photos: list[str] | None = Field(default=None, description="Ссылки для получения фото")

    @model_validator(mode="before")
    def pre_images_list(cls, data: Any) -> Any:
        """Обработка изображений"""
        if isinstance(data, dict):
            for field_name, param_keys in ImagesSchema.thumbor_params.items():
                if isinstance(data.get(field_name), list):
                    items = []
                    for item in data[field_name]:
                        if isinstance(item, dict):
                            src = item.get("url")
                            image_width = item.get("image_width")
                            image_height = item.get("image_height")
                        else:
                            src = item
                            image_width = None
                            image_height = None

                        if isinstance(src, str) and not src.startswith("http"):
                            items.append(
                                get_thumbor_image_url(
                                    src,
                                    param_keys.get(cls.view_action, param_keys.get("all")),
                                    cls.image_params,
                                    image_width,
                                    image_height,
                                )
                            )

                    data[field_name] = items

        return data


BaseModelType = TypeVar("BaseModelType", bound=BaseModel)
