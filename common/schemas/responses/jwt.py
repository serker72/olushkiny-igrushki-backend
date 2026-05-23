from pydantic import BaseModel, Field

from common.schemas.models import JwtTokenInfoModel, JwtTokenModel


class JwtTokenRefreshResponse(BaseModel):
    """Схема данных с информацией об обновленных JWT токенах"""

    access_token: JwtTokenModel | JwtTokenInfoModel = Field(description="Данные JWT access токена")
    refresh_token: JwtTokenInfoModel = Field(description="Данные JWT refresh токена")
