from app_backend.services.base import BaseModelService
from app_backend.services.user_authorization_codes import UserAuthorizationCodeService, UserLogin
from common.enums import UserRegistrationCodeStatuses
from common.exceptions import ForbiddenException
from common.models import User, UserRegistrationCode
from common.schemas.requests import UserRegistrationCodeRequest


class UserRegistrationCodeService(UserAuthorizationCodeService, BaseModelService):
    """Сервис для работы с кодами подтверждения регистрации пользователей"""

    model_class = UserRegistrationCode
    model_status_class = UserRegistrationCodeStatuses
    template_event_code: str = "user_sign_up_request_code"

    async def user_validate(
        self,
        user: User | None,
        data: UserRegistrationCodeRequest,
        user_login: UserLogin,
    ):
        """Валидация логина пользователя"""
        if user is not None:
            raise ForbiddenException(code=f"sign_up_user_by_{user_login.field}_already_exists")
