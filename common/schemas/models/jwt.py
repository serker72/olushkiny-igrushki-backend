from datetime import datetime

from pydantic import BaseModel, Field


class JwtTokenModel(BaseModel):
    """Схема данных JWT токена"""

    token: str = Field(description="Токен")
    jti: str = Field(description="ID токена")
    exp: datetime = Field(description="Срок действия токена")


class JwtTokenInfoModel(BaseModel):
    """Схема данных с информацией о JWT токене"""

    jti: str = Field(description="ID токена")
    exp: datetime = Field(description="Срок действия токена")
