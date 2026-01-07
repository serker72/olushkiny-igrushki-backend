from datetime import date

from pydantic import ConfigDict, Field

from common.schemas.models import (
    EmailOrPhoneSchema,
    EmailSchema,
    PhoneOptionalSchema,
    UserConfirmationCodeCommonData,
    UserDeviceData,
    UserFullNameData,
    UserTimeZoneNameData,
)
from common.schemas.models.settings import settings


class UserAuthorizationCodeRequest(UserConfirmationCodeCommonData):
    """Схема запроса отправки кода подтверждения при авторизации пользователя"""


class UserRegistrationCodeRequest(UserConfirmationCodeCommonData):
    """Схема запроса отправки кода подтверждения при регистрации пользователя"""


class UserSignInRequest(UserConfirmationCodeCommonData):
    """Схема запроса авторизации пользователя"""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        description="Код подтверждения авторизации", max_length=settings.backend_user_confirmation_code_length
    )


class UserRegistrationCodeVerifyRequest(UserConfirmationCodeCommonData):
    """Схема запроса проверки кода подтверждения при регистрации пользователя"""

    code: str = Field(
        description="Код подтверждения регистрации", max_length=settings.backend_user_confirmation_code_length
    )


# class UserSignUpVerifyLoginRequest(EmailOrPhoneSchema):
class UserSignUpVerifyLoginRequest(EmailSchema):
    """Схема запроса проверки логина при регистрации"""

    model_config = ConfigDict(extra="forbid")


# class UserSignUpRequest(EmailAndOrPhoneSchema, UserFullNameData, UserTimeZoneNameData, UserDeviceData):
class UserSignUpRequest(EmailSchema, PhoneOptionalSchema, UserFullNameData, UserTimeZoneNameData, UserDeviceData):
    """Схема запроса регистрации пользователя"""

    model_config = ConfigDict(extra="forbid")

    birthday: date | None = Field(default=None, description="Дата рождения")
    confirmation_code_id: int = Field(description="ID кода подтверждения")


class UserConfirmationCodeIgnoreRequest(EmailOrPhoneSchema):
    """Схема запроса игнорирования кодов подтверждения"""

    model_config = ConfigDict(extra="forbid")


class UserUpdateProfileRequest(PhoneOptionalSchema, UserFullNameData, UserTimeZoneNameData):
    """Схема запроса изменения данных текущего пользователя"""

    model_config = ConfigDict(extra="forbid")

    birthday: date | None = Field(default=None, description="Дата рождения")
