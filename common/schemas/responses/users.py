from datetime import datetime

from pydantic import BaseModel, Field

from common.schemas.models import EmailOrPhoneSchema, JwtTokenInfoModel, JwtTokenModel, UserModel

from .base import BaseRetrieveCollectionPaginateResponse, BaseRetrieveCollectionResponse, BaseRetrieveResponse


class UserSignInResponse(BaseModel):
    """Схема ответа с данными авторизации пользователя"""

    user: UserModel = Field(description="Данные пользователя")
    access_token: JwtTokenModel | JwtTokenInfoModel = Field(description="Данные JWT access токена")
    refresh_token: JwtTokenInfoModel = Field(description="Данные JWT refresh токена")


class UserSignUpResponse(BaseModel):
    """Схема ответа с данными регистрации пользователя"""

    user: UserModel = Field(description="Данные пользователя")
    access_token: JwtTokenModel = Field(description="Данные JWT access токена")
    refresh_token: JwtTokenInfoModel = Field(description="Данные JWT refresh токена")


class UserRetrieveResponse(BaseRetrieveResponse):
    """Схема ответа с данными пользователя"""

    item: UserModel = Field(description="Данные пользователя")


class UserRetrieveCollectionResponse(BaseRetrieveCollectionResponse):
    """Схема ответа со списком пользователей"""

    items: list[UserModel] = Field(description="Список пользователей")


class UserRetrieveCollectionPaginateResponse(BaseRetrieveCollectionPaginateResponse):
    """Схема ответа со списком пользователей с пагинацией"""

    items: list[UserModel] = Field(description="Список пользователей")


class UserConfirmationCodeResponse(BaseModel):
    """Схема ответа на запрос получения кода подтверждения"""

    confirmation_code_lifetime: datetime = Field(description="Время окончания срока действия кода подтверждения")
    confirmation_code_next_attempt_timeout: int = Field(
        description="Таймаут выполнения следующей попытки получения кода подтверждения в секундах"
    )


class UserRegistrationCodeVerifyResponse(BaseModel):
    """Схема ответа на запрос проверки кода подтверждения при регистрации"""

    is_verified: bool = Field(description="Флаг успешной проверки кода подтверждения")
    confirmation_code_id: int = Field(description="ID кода подтверждения")


class UserConfirmationCodeIgnoreResponse(BaseModel):
    """Схема ответа на запрос игнорирования кодов подтверждения"""

    is_ignored: bool = Field(description="Флаг игнорирования кодов подтверждения")


class UserSignUpVerifyLoginResponse(EmailOrPhoneSchema):
    """Схема ответа на запрос проверки логина при регистрации"""

    is_verified: bool = Field(description="Флаг успешной проверки логина")
