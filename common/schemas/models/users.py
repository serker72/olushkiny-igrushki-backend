from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic_extra_types.timezone_name import TimeZoneName

from common.helpers import constants as c

from .base import (
    AuditModel,
    # EmailAndOrPhoneSchema,
    # EmailOptionalSchema,
    # EmailOrPhoneSchema,
    EmailSchema,
    ImageSchema,
    PhoneOptionalSchema,
    # PhoneSchema,
)
from .module_states import ModuleStateModel
from .settings import settings


class UserModel(AuditModel, ImageSchema):
    """Схема данных пользователя"""

    thumbor_params = {
        "photo": {
            # "all": "w200_h200_webp",
            # "retrieve": "w720_h1280_webp",
            "retrieve_collection": "w200_h200_webp",
        },
    }

    id: int = Field(description="ID пользователя")
    state_id: int = Field(description="ID статуса")
    surname: str = Field(description="Фамилия")
    name: str = Field(description="Имя")
    second_name: str | None = Field(description="Отчество")
    email: str = Field(description="Адрес E-Mail")
    phone: str | None = Field(description="Номер телефона")
    birthday: date | None = Field(description="Дата рождения")
    time_zone: TimeZoneName = Field(description="Часовой пояс пользователя")
    last_logged_on: datetime | None = Field(description="Время последней авторизации")

    state: ModuleStateModel = Field(description="Данные статуса пользователя")


class UserRegistrationCodeModel(AuditModel):
    """Схема данных кода подтверждения при регистрации пользователя"""

    device_id: UUID = Field(description="ID устройства")
    email: str = Field(description="Адрес E-Mail")
    # phone: str | None = Field(description="Номер телефона")
    code: str = Field(description="Код подтверждения", max_length=settings.backend_user_confirmation_code_length)
    status: str = Field(description="Статус")
    group_number: int | None = Field(description="Номер группы сгенерированных кодов")
    user_id: int | None = Field(description="ID пользователя")


class UserAuthorizationCodeModel(UserRegistrationCodeModel):
    """Схема данных кода подтверждения при авторизации пользователя"""

    user_id: int = Field(description="ID пользователя")


class UserConfirmationCodeModel(BaseModel):
    """Схема данных кода подтверждения"""

    code_type: str = Field(None, description="Тип кода подтверждения")
    device_id: str = Field(None, description="ID устройства")
    email: str = Field(description="Адрес E-Mail")
    # phone: str | None = Field(description="Номер телефона")
    code: str = Field(description="Код подтверждения", max_length=settings.backend_user_confirmation_code_length)
    status: str = Field(description="Статус")
    created_on: datetime = Field(description="Время создания")


class UserFullNameData(BaseModel):
    """Схема данных ФИО пользователя"""

    surname: str = Field(description="Фамилия")
    name: str = Field(description="Имя", min_length=2)
    second_name: str | None = Field(default=None, description="Отчество")


class UserDeviceData(BaseModel):
    """Схема данных устройства пользователя"""

    user_device_id: str = Field(description="ID устройства")
    # user_agent: str = Field(description="User Agent")


class UserTimeZoneNameData(BaseModel):
    """Схема данных часового пояса пользователя"""

    time_zone: TimeZoneName | None = Field(c.USER_DEFAULT_TIME_ZONE, description="Часовой пояс")


# class UserConfirmationCodeCommonData(EmailOrPhoneSchema, UserDeviceData, UserTimeZoneNameData):
class UserConfirmationCodeCommonData(EmailSchema, UserDeviceData, UserTimeZoneNameData):
    """Схема общих данных запроса отправки кода подтверждения"""

    model_config = ConfigDict(extra="forbid")


# class UserUpdateProfileData(UserFullNameData, EmailOptionalSchema, PhoneOptionalSchema, UserTimeZoneNameData):
class UserUpdateProfileData(UserFullNameData, PhoneOptionalSchema, UserTimeZoneNameData):
    """Схема запроса изменения данных текущего пользователя"""

    model_config = ConfigDict(extra="forbid")
