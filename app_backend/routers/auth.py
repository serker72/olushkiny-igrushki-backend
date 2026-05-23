from inspect import stack

from classy_fastapi import Routable, get, post
from fastapi import Request, Response, status
from fastapi.responses import HTMLResponse
from loguru import logger

from app_backend.routers.base import BaseRouter, BaseUIRouter
from app_backend.services.base import BaseServiceType
from common.exceptions import get_responses
from common.helpers import constants as c
from common.schemas.models import JwtTokenInfoModel, JwtTokenModel
from common.schemas.requests import (
    UserAuthorizationCodeRequest,
    UserRegistrationCodeRequest,
    UserRegistrationCodeVerifyRequest,
    UserSignInRequest,
    UserSignUpRequest,
)
from common.schemas.responses import (
    CustomJSONResponse,
    JwtTokenRefreshResponse,
    UserConfirmationCodeResponse,
    UserRegistrationCodeVerifyResponse,
    UserSignInResponse,
    UserSignUpResponse,
)


class AuthRouter(BaseRouter, Routable):
    """Класс представления для регистрации и авторизации пользователей"""

    prefix = "/auth"
    tags = ["Регистрация и авторизация пользователей"]
    is_security_dependency = False
    security_dependency_endpoints = ["/sign-out"]

    def response_with_access_token_cookie(
        self,
        user_service: BaseServiceType,
        access_token: JwtTokenModel | None,
        response: CustomJSONResponse | Response,
    ) -> CustomJSONResponse:
        """Установка cookie access_token для ответа"""
        response.set_cookie(
            key=user_service.settings.authjwt_access_cookie_key,
            value=access_token.token if access_token else "",
            httponly=True,
            secure=user_service.settings.authjwt_cookie_secure,
            samesite="lax",
            max_age=user_service.settings.authjwt_access_token_expires,
            domain=f".{user_service.settings.authjwt_cookie_domain}",
        )
        return response

    def response_with_refresh_token_cookie(
        self,
        user_service: BaseServiceType,
        refresh_token: JwtTokenModel | None,
        response: CustomJSONResponse | Response,
    ) -> CustomJSONResponse:
        """Установка cookie refresh_token для ответа"""
        response.set_cookie(
            key=user_service.settings.authjwt_refresh_cookie_key,
            value=refresh_token.token if refresh_token else "",
            httponly=True,
            secure=user_service.settings.authjwt_cookie_secure,
            samesite="lax",
            max_age=user_service.settings.authjwt_refresh_token_expires,
            domain=f".{user_service.settings.authjwt_cookie_domain}",
            path=f"{user_service.settings.backend_api_prefix}{self.prefix}/token-refresh",
        )
        return response

    @post(
        "/sign-in-request-code",
        summary="Получение кода подтверждения авторизации пользователя",
        response_model=UserConfirmationCodeResponse,
        responses=get_responses([status.HTTP_401_UNAUTHORIZED]),
    )
    async def sign_in_request_code(
        self, request: Request, request_data: UserAuthorizationCodeRequest
    ) -> UserConfirmationCodeResponse:
        """Получение кода подтверждения авторизации пользователя"""
        user_confirmation_code_service = self.get_service(
            stack()[0].function, request, c.MODULE_CODE_USER_AUTHORIZATION_CODES
        )
        entity = await user_confirmation_code_service.create(request_data)
        return user_confirmation_code_service.get_user_confirmation_code_response(entity, request_data.time_zone)

    @post(
        "/sign-in",
        summary="Авторизация пользователя",
        response_model=UserSignInResponse,
        responses=get_responses([status.HTTP_401_UNAUTHORIZED]),
    )
    async def sign_in(self, request: Request, request_data: UserSignInRequest) -> CustomJSONResponse:
        """Авторизация пользователя"""
        user_service = self.get_service(stack()[0].function, request, c.MODULE_CODE_USERS)
        item, access_token, refresh_token = await user_service.sign_in(request_data)
        result = UserSignInResponse(
            user=item,
            # access_token=access_token,
            access_token=JwtTokenInfoModel(jti=access_token.jti, exp=access_token.exp),
            refresh_token=JwtTokenInfoModel(jti=refresh_token.jti, exp=refresh_token.exp),
        )
        response = CustomJSONResponse(status_code=status.HTTP_200_OK, content=result.model_dump())
        # return self.response_with_refresh_token_cookie(user_service, refresh_token, response)
        return self.response_with_refresh_token_cookie(
            user_service,
            refresh_token,
            self.response_with_access_token_cookie(user_service, access_token, response),
        )

    # @post(
    #     "/sign-up-request-code",
    #     summary="Получение кода подтверждения регистрации пользователя",
    #     response_model=UserConfirmationCodeResponse,
    #     responses=get_responses([status.HTTP_403_FORBIDDEN]),
    # )
    # async def sign_up_request_code(
    #     self, request: Request, request_data: UserRegistrationCodeRequest
    # ) -> UserConfirmationCodeResponse:
    #     """Получение кода подтверждения регистрации пользователя"""
    #     user_confirmation_code_service = self.get_service(
    #         stack()[0].function, request, c.MODULE_CODE_USER_REGISTRATION_CODES
    #     )
    #     entity = await user_confirmation_code_service.create(request_data)
    #     return user_confirmation_code_service.get_user_confirmation_code_response(entity, request_data.time_zone)
    #
    # @post(
    #     "/sign-up-verify-code",
    #     summary="Проверка кода подтверждения регистрации пользователя",
    #     response_model=UserRegistrationCodeVerifyResponse,
    #     responses=get_responses([status.HTTP_403_FORBIDDEN]),
    # )
    # async def sign_up_verify_code(
    #     self, request: Request, request_data: UserRegistrationCodeVerifyRequest
    # ) -> UserRegistrationCodeVerifyResponse:
    #     """Проверка кода подтверждения регистрации пользователя"""
    #     user_service = self.get_service(stack()[0].function, request, c.MODULE_CODE_USERS)
    #     return await user_service.sign_up_verify_code(request_data)
    #
    # @post(
    #     "/sign-up",
    #     summary="Регистрация пользователя",
    #     response_model=UserSignUpResponse,
    #     responses=get_responses([status.HTTP_403_FORBIDDEN]),
    # )
    # async def sign_up(self, request: Request, request_data: UserSignUpRequest) -> CustomJSONResponse:
    #     """Регистрация пользователя"""
    #     user_service = self.get_service(stack()[0].function, request, c.MODULE_CODE_USERS)
    #     item, access_token, refresh_token = await user_service.sign_up(request_data)
    #     result = UserSignUpResponse(
    #         user=item,
    #         access_token=access_token,
    #         refresh_token=JwtTokenInfoModel(jti=refresh_token.jti, exp=refresh_token.exp),
    #     )
    #     response = CustomJSONResponse(status_code=status.HTTP_200_OK, content=result.model_dump())
    #     return self.response_with_refresh_token_cookie(user_service, refresh_token, response)

    @post(
        "/token-refresh",
        summary="Обновление JWT токенов пользователя",
        response_model=JwtTokenRefreshResponse,
        responses=get_responses([status.HTTP_403_FORBIDDEN]),
    )
    async def token_refresh(self, request: Request) -> CustomJSONResponse:
        """Обновление JWT токенов пользователя"""
        user_service = self.get_service(stack()[0].function, request, c.MODULE_CODE_USERS)
        access_token, refresh_token = await user_service.token_refresh(request.state.verified_token)
        response = CustomJSONResponse(
            status_code=status.HTTP_200_OK,
            content=JwtTokenRefreshResponse(
                # access_token=access_token,
                access_token=(JwtTokenInfoModel(jti=access_token.jti, exp=access_token.exp)),
                refresh_token=(JwtTokenInfoModel(jti=refresh_token.jti, exp=refresh_token.exp)),
            ),
        )

        if isinstance(refresh_token, JwtTokenModel):
            # return self.response_with_refresh_token_cookie(user_service, refresh_token, response)
            return self.response_with_refresh_token_cookie(
                user_service,
                refresh_token,
                self.response_with_access_token_cookie(user_service, access_token, response),
            )

        # return response
        return self.response_with_access_token_cookie(user_service, access_token, response)

    @post(
        "/sign-out",
        summary="Завершение сеанса пользователя",
        responses=get_responses([status.HTTP_403_FORBIDDEN]),
    )
    async def sign_out(self, request: Request) -> Response:
        """Завершение сеанса пользователя"""
        user_service = self.get_service(stack()[0].function, request, c.MODULE_CODE_USERS)
        await user_service.sign_out(request.state.verified_token)
        response = Response(status_code=status.HTTP_204_NO_CONTENT)
        return self.response_with_refresh_token_cookie(user_service, None, response)


class AuthUIRouter(BaseUIRouter, Routable):
    """Класс представления UI для регистрации и авторизации пользователей"""

    prefix = "/auth"
    tags = ["Регистрация и авторизация пользователей"]
    is_security_dependency = False

    @property
    def template_aliases(self) -> dict:
        """Словарь соответствия алиасов и имен файлов шаблонов"""
        return {
            "sign_in": "page/auth.html",
        }

    @get("/sign-in")
    async def sign_in(self, request: Request) -> HTMLResponse:
        """Получение страницы авторизации пользователя"""
        return await self.build_template_response(request, "sign_in", {})
