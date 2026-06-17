import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any

from loguru import logger
from redis.asyncio import Redis
from sqlalchemy import desc

from app_backend.services.base import BaseModelService
from common.enums import UserAuthorizationCodeStatuses, UserRegistrationCodeStatuses
from common.exceptions import ForbiddenException, UnauthorizedException
from common.helpers import constants as c
from common.helpers import json, timeutil
from common.helpers.lock import task_lock
from common.helpers.redis_async import get_async_redis
from common.models import Device, User, UserAuthorizationCode, UserDevice, UserRegistrationCode
from common.schemas.models import JwtTokenInfoModel, JwtTokenModel, UserModel
from common.schemas.requests import (
    UserDeviceCreateRequest,
    UserRegistrationCodeVerifyRequest,
    UserSignInRequest,
    UserSignUpRequest,
)
from common.schemas.responses import (
    UserRegistrationCodeVerifyResponse,
    UserRetrieveResponse,
)


class UserService(BaseModelService):
    """Сервис для работы с пользователями"""

    model_class = User
    schemas = {"update": UserRetrieveResponse}

    @task_lock("save_user_list_to_cache")
    async def save_user_list_to_cache(self):
        """Сохранение списка пользователей в кеше Redis"""
        redis_connection = await get_async_redis()
        entities = await self.get_entities(self.model_class)
        for entity in entities:
            key = c.REDIS_KEY_USER_LIST_KEY.format(user_id=entity.id)
            item = await self.entity_to_schema(entity)
            await redis_connection.hset(c.REDIS_KEY_USER_LIST_HASH, key, json.dumps(item.model_dump()))

    @staticmethod
    def sign_in_check_user_state(entity: User, field_title: str, field_value: Any):
        """Проверка статуса пользователя при авторизации"""
        if entity.state.code == c.STATE_DELETED:
            raise ForbiddenException(
                code=f"user_is_{entity.state.code}",
                message_context={"field_title": field_title, "field_value": field_value},
            )

    async def verify_confirmation_code(
        self,
        data: UserSignInRequest | UserRegistrationCodeVerifyRequest,
        dt_current: datetime = None,
    ) -> tuple[Device, UserDevice, UserAuthorizationCode | UserRegistrationCode]:
        """Проверка кода подтверждения"""
        logger.debug(f"data={repr(data.model_dump())}")
        logger.debug(f"self.user_agent={self.user_agent}")

        dt_current = dt_current or timeutil.utcnow()

        model_class = (
            UserRegistrationCode if isinstance(data, UserRegistrationCodeVerifyRequest) else UserAuthorizationCode
        )
        model_status_class = (
            UserRegistrationCodeStatuses
            if isinstance(data, UserRegistrationCodeVerifyRequest)
            else UserAuthorizationCodeStatuses
        )
        exception_class = UnauthorizedException if isinstance(data, UserSignInRequest) else ForbiddenException

        device: Device = await self.get_entity_by_filters(
            Device,
            [
                Device.device_id == data.user_device_id,
                Device.user_agent == self.user_agent,
            ],
            exception_code="confirmation_code_device_not_found",
            exception_class=exception_class,
        )
        # logger.debug(f"device.user_agent={device.user_agent}, self.user_agent={self.user_agent}")
        # if device.user_agent != self.user_agent:
        #     raise exception_class(code="confirmation_code_device_not_match")

        orders = [desc(model_class.created_on)]
        last_code: UserAuthorizationCode | UserRegistrationCode = await self.get_entity_by_filters(
            model_class,
            [
                model_class.device_id == device.id,
                (
                    model_class.email == data.email
                    if hasattr(data, "email") and data.email
                    else model_class.phone == data.phone
                ),
                model_class.code == data.code,
            ],
            exception_code="confirmation_code_not_found",
            orders=orders,
            exception_class=exception_class,
        )
        logger.debug(f"last_code={repr(await last_code.as_dict())}")

        if last_code.status != model_status_class.created:
            raise exception_class(code=f"confirmation_code_is_{last_code.status.name}")

        if (dt_current - last_code.created_on).total_seconds() > self.settings.backend_user_confirmation_code_lifetime:
            raise exception_class(code="confirmation_code_is_expired")

        if last_code.user_id:
            if last_code.email and last_code.email != last_code.user.email:
                raise exception_class(code="confirmation_code_email_not_match")
            elif last_code.phone and last_code.phone != last_code.user.phone:
                raise exception_class(code="confirmation_code_phone_not_match")

            user_device: UserDevice | None = await self.get_entity_by_filters(
                UserDevice,
                [UserDevice.device_id == device.id, UserDevice.user_id == last_code.user.id],
                exception_code="confirmation_code_device_not_match",
                exception_class=exception_class,
            )
        else:
            user_device = None

        return device, user_device, last_code

    async def add_jtw_token_to_active_list(self, redis_connection: Redis, hash_name: str, token: str) -> JwtTokenModel:
        """Сохранение информации о токене в списке активных токенов"""
        token_data = self.jwt_auth.get_raw_jwt(token)
        dt_token_expired = datetime.fromtimestamp(token_data.get("exp"), timezone.utc)
        dt_diff = dt_token_expired - timeutil.utcnow()
        key = c.REDIS_KEY_JWT_ACTIVELIST_KEY.format(type=token_data.get("type"), jti=token_data.get("jti"))
        await redis_connection.hset(hash_name, key, str(token_data.get("exp")))
        await redis_connection.hexpire(hash_name, dt_diff, key)
        return JwtTokenModel(token=token, jti=token_data.get("jti"), exp=dt_token_expired)

    async def revoke_user_device_all_tokens(
        self, redis_connection: Redis, user_id: int | str, user_device_id: str, refresh_token_jti: str = None
    ) -> None:
        """Отзыв всех активных токенов пользователя для устройства"""
        dt_current = timeutil.utcnow()
        hash_name = c.REDIS_KEY_JWT_ACTIVELIST_HASH.format(user_id=user_id, user_device_id=user_device_id)
        tokens = await redis_connection.hgetall(hash_name)
        for key, value in tokens.items():
            key_parts = key.split(":")

            # Пропускаем refresh_token
            if refresh_token_jti == key_parts[1]:
                continue

            dt_token_expired = datetime.fromtimestamp(int(value), timezone.utc)
            dt_diff = dt_token_expired - dt_current
            await redis_connection.setex(
                c.REDIS_KEY_JWT_BLACKLIST.format(type=key_parts[0], jti=key_parts[1]), dt_diff, "true"
            )
            await redis_connection.hdel(hash_name, key)

    async def revoke_user_all_device_tokens(self, redis_connection: Redis, user_id: int) -> None:
        """Отзыв всех активных токенов пользователя для всех устройства"""
        async for key in redis_connection.scan_iter(c.REDIS_KEY_JWT_ACTIVELIST_HASH_PATTERN.format(user_id=user_id)):
            key_parts = key.decode("utf-8").split(":")
            await self.revoke_user_device_all_tokens(redis_connection, user_id, key_parts[1])

    async def generate_jtw_tokens(
        self,
        user: User,
        device: Device,
        is_refresh_token_required: bool = True,
        refresh_token_jti: str = None,
    ) -> tuple[JwtTokenModel, JwtTokenModel | None]:
        """
        Генерация JWT токенов.

        Перед генерацией нового refresh токена:
        - получение списка активных токенов пользователя для устройства
        - добавление всех активных токенов в список отозванных
        - удаление всех активных токенов из списка активных
        """
        redis_connection = await get_async_redis()

        user_device_id = f"{device.device_id}::{device.user_agent}"
        user_device_id_hash = hmac.new(
            self.settings.backend_password_secret_key.encode("utf-8"), user_device_id.encode("utf-8"), hashlib.sha3_512
        ).hexdigest()

        hash_name = c.REDIS_KEY_JWT_ACTIVELIST_HASH.format(user_id=user.id, user_device_id=user_device_id_hash)

        if is_refresh_token_required or refresh_token_jti:
            await self.revoke_user_device_all_tokens(redis_connection, user.id, user_device_id_hash, refresh_token_jti)

        user_claims = {
            "fio": user.fio,
            "email": user.email,
            "phone": user.phone,
            "device_id": device.device_id,
            "user_agent": device.user_agent,
        }

        token = self.jwt_auth.create_access_token(subject=str(user.id), user_claims=user_claims)
        access_token = await self.add_jtw_token_to_active_list(redis_connection, hash_name, token)

        if is_refresh_token_required is True:
            token = self.jwt_auth.create_refresh_token(subject=str(user.id), user_claims=user_claims)
            refresh_token = await self.add_jtw_token_to_active_list(redis_connection, hash_name, token)
        else:
            refresh_token = None

        return access_token, refresh_token

    async def sign_in(self, data: UserSignInRequest) -> tuple[UserModel, JwtTokenModel, JwtTokenModel]:
        """Авторизация пользователя с использованием кода подтверждения"""
        dt_current = timeutil.utcnow()
        device, user_device, last_code = await self.verify_confirmation_code(data, dt_current)
        access_token, refresh_token = await self.generate_jtw_tokens(last_code.user, device, True)
        logger.debug(
            f"access_token: {repr(access_token.model_dump())}, refresh_token: {repr(refresh_token.model_dump())}"
        )

        user_device.last_logged_on = dt_current
        user_device.updated_on = dt_current
        user_device.updated_by = last_code.user.id
        await self.flush_and_refresh_entity(user_device)

        last_code.user.last_logged_on = dt_current
        last_code.user.updated_on = dt_current
        last_code.user.updated_by = last_code.user.id
        await self.flush_and_refresh_entity(last_code.user)

        last_code.status = UserAuthorizationCodeStatuses.confirmed
        last_code.updated_on = dt_current
        last_code.updated_by = last_code.user.id
        await self.flush_and_refresh_entity(last_code)

        return UserModel(**await last_code.user.as_dict()), access_token, refresh_token

    async def sign_up_verify_code(self, data: UserRegistrationCodeVerifyRequest) -> UserRegistrationCodeVerifyResponse:
        """Проверка кода подтверждения регистрации"""
        dt_current = timeutil.utcnow()
        device, user_device, last_code = await self.verify_confirmation_code(data, dt_current)

        last_code.status = UserRegistrationCodeStatuses.confirmed
        last_code.updated_on = dt_current
        last_code.updated_by = self.user_id or 1
        await self.flush_and_refresh_entity(last_code)

        return UserRegistrationCodeVerifyResponse(is_verified=True, confirmation_code_id=last_code.id)

    async def sign_up(self, data: UserSignUpRequest) -> tuple[UserModel, JwtTokenModel, JwtTokenModel]:
        """Регистрация нового пользователя"""
        dt_current = timeutil.utcnow()

        confirmation_code: UserRegistrationCode = await self.get_entity(
            UserRegistrationCode,
            data.confirmation_code_id,
            exception_code="confirmation_code_not_found",
            exception_class=ForbiddenException,
        )

        if confirmation_code.status != UserRegistrationCodeStatuses.confirmed:
            raise ForbiddenException(code=f"confirmation_code_is_{confirmation_code.status.name}")
        if confirmation_code.email and confirmation_code.email != data.email:
            raise ForbiddenException(code="confirmation_code_email_not_match")
        if confirmation_code.phone and confirmation_code.phone != data.phone:
            raise ForbiddenException(code="confirmation_code_phone_not_match")

        device: Device = await self.get_entity(
            Device,
            data.user_device_id,
            "device_id",
            "ID устройства",
            exception_code="confirmation_code_device_not_found",
            exception_class=ForbiddenException,
        )
        if device.user_agent != self.user_agent:
            raise ForbiddenException(code="confirmation_code_device_not_match")

        entity_schema: UserModel = await self.create(data)
        entity: User = await self.get_entity(User, entity_schema.id)

        entity.last_logged_on = dt_current
        entity.updated_on = dt_current
        entity.updated_by = entity.id
        await self.flush_and_refresh_entity(entity)

        confirmation_code.status = UserRegistrationCodeStatuses.completed
        confirmation_code.updated_on = dt_current
        confirmation_code.updated_by = entity.id
        confirmation_code.user_id = entity.id
        await self.flush_and_refresh_entity(confirmation_code)

        user_device_service = self.get_service(c.MODULE_CODE_USER_DEVICES)
        await user_device_service.create(
            UserDeviceCreateRequest(user_id=entity.id, device_id=device.id, last_logged_on=dt_current)
        )

        access_token, refresh_token = await self.generate_jtw_tokens(entity, device, True)

        return UserModel(**await entity.as_dict()), access_token, refresh_token

    async def after_entity_create(self, entity: User, data: UserSignUpRequest):
        """Выполнение дополнительных действия после создания объекта"""
        await self.save_user_list_to_cache()

    async def verify_token_user_and_device(self, verified_token: dict) -> tuple[User, Device]:
        """Проверка пользователя и устройства из JWT токена"""
        entity: User = await self.get_entity(
            User,
            self.user_id,
            exception_code="user_not_found_by_id",
            exception_class=ForbiddenException,
        )

        device: Device = await self.get_entity(
            Device,
            verified_token.get("device_id"),
            "device_id",
            "ID устройства",
            exception_code="device_not_found_by_device_id",
            exception_class=ForbiddenException,
        )
        if device.user_agent != self.user_agent:
            raise ForbiddenException(code="device_not_found_by_device_id")

        await self.get_entity_by_filters(
            UserDevice,
            [UserDevice.device_id == device.id, UserDevice.user_id == entity.id],
            exception_code="device_not_found_by_device_id",
            exception_class=ForbiddenException,
        )

        return entity, device

    async def token_refresh(self, verified_token: dict) -> tuple[JwtTokenModel, JwtTokenModel | JwtTokenInfoModel]:
        """Обновление JWT access токена пользователя"""
        entity, device = await self.verify_token_user_and_device(verified_token)

        dt_refresh_token_expired = datetime.fromtimestamp(verified_token["exp"], timezone.utc)
        dt_current = timeutil.utcnow()
        logger.debug(
            f"diff: {dt_refresh_token_expired - dt_current}, {(dt_refresh_token_expired - dt_current).total_seconds()}"
        )
        logger.debug(f"authjwt_access_token_expires: {self.settings.authjwt_access_token_expires}")
        logger.debug(f"dt_refresh_token_expired > dt_current: {dt_refresh_token_expired > dt_current}")
        is_refresh_token_required = (
            (dt_refresh_token_expired - dt_current).total_seconds() <= self.settings.authjwt_access_token_expires
            if dt_refresh_token_expired > dt_current
            else True
        )

        access_token, refresh_token = await self.generate_jtw_tokens(
            entity,
            device,
            is_refresh_token_required,
            verified_token.get("jti") if not is_refresh_token_required else None,
        )
        return access_token, refresh_token or JwtTokenInfoModel(jti=verified_token["jti"], exp=dt_refresh_token_expired)

    async def sign_out(self, verified_token: dict) -> None:
        """Завершение сеанса пользователя"""
        user_device_id = f"{verified_token.get('device_id')}::{self.user_agent}"
        user_device_id_hash = hmac.new(
            self.settings.backend_password_secret_key.encode("utf-8"), user_device_id.encode("utf-8"), hashlib.sha3_512
        ).hexdigest()
        redis_connection = await get_async_redis()
        await self.revoke_user_device_all_tokens(redis_connection, self.user_id, user_device_id_hash)
