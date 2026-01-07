from dataclasses import dataclass
from datetime import timedelta

from loguru import logger
from pydantic_extra_types.timezone_name import TimeZoneName
from sqlalchemy import desc, func, select, update

from app_backend.services.base import BaseModelService
from common.enums import UserAuthorizationCodeStatuses
from common.exceptions import ConflictException, ForbiddenException
from common.helpers import constants as c
from common.helpers import timeutil
from common.helpers.date_time import get_datetime_as_timezone
from common.helpers.password import generate_password, get_password_characters
from common.models import Device, User, UserAuthorizationCode, UserDevice
from common.schemas.models import UserAuthorizationCodeModel, UserRegistrationCodeModel
from common.schemas.requests import (
    DeviceCreateRequest,
    UserAuthorizationCodeRequest,
    UserConfirmationCodeIgnoreRequest,
    UserDeviceCreateRequest,
    UserRegistrationCodeRequest,
)
from common.schemas.responses import UserConfirmationCodeResponse


@dataclass
class UserLogin:
    """Класс поля логина пользователя"""

    field: str
    value: str
    title: str


class UserAuthorizationCodeService(BaseModelService):
    """Сервис для работы с кодами подтверждения авторизации пользователей"""

    model_class = UserAuthorizationCode
    model_status_class = UserAuthorizationCodeStatuses

    is_create_event_registration = False
    is_update_event_registration = False
    is_change_state_event_registration = False
    is_delete_event_registration = False

    template_event_code: str = "user_sign_in_request_code"

    @staticmethod
    def get_user_login(
        data: UserAuthorizationCodeRequest | UserRegistrationCodeRequest,
        # | UserEmailConfirmCodeRequest
        # | UserPhoneConfirmCodeRequest,
    ) -> UserLogin:
        """Получение данных о логине пользователя"""
        return UserLogin(
            field=c.USER_LOGIN_EMAIL if hasattr(data, "email") and data.email else c.USER_LOGIN_PHONE,
            value=data.email if hasattr(data, "email") and data.email else data.phone,
            title=c.USER_LOGIN_TITLE_EMAIL if hasattr(data, "email") and data.email else c.USER_LOGIN_TITLE_PHONE,
        )

    async def user_validate(
        self,
        user: User | None,
        data: UserAuthorizationCodeRequest,  # | UserEmailConfirmCodeRequest | UserPhoneConfirmCodeRequest,
        user_login: UserLogin,
    ):
        """Валидация логина пользователя"""
        if user is None:
            raise ForbiddenException(code=f"sign_in_user_by_{user_login.field}_not_exists")

        # if isinstance(data, UserAuthorizationCodeRequest) and not getattr(
        #     user, f"is_{user_login.field}_confirmed", False
        # ):
        #     raise ForbiddenException(code=f"sign_in_{user_login.field}_not_confirmed")

        if user.state.code == c.STATE_DELETED:
            raise ForbiddenException(
                code=f"user_is_{user.state.code}",
                message_context={"field_title": user_login.title, "field_value": user_login.value},
            )

        self.entity_create_additional_fields["user_id"] = user.id

    async def entity_validate(
        self,
        entity: UserAuthorizationCode,
        data: UserAuthorizationCodeRequest | UserRegistrationCodeRequest,
        # | UserEmailConfirmCodeRequest
        # | UserPhoneConfirmCodeRequest,
        action: str,
    ):
        """Валидация данных объекта"""
        dt = timeutil.utcnow()

        device: Device | None = await self.get_entity_by_filters(
            Device,
            [
                Device.device_id == data.user_device_id,
                Device.user_agent == self.user_agent,
            ],
            is_raise_exception=False,
        )
        if not device:
            device_service = self.get_service(c.MODULE_CODE_DEVICES)
            device = await device_service.create(
                DeviceCreateRequest(device_id=data.user_device_id, user_agent=self.user_agent)
            )

        user_login: UserLogin = self.get_user_login(data)

        user: User | None = await self.get_entity(User, user_login.value, user_login.field, is_raise_exception=False)

        await self.user_validate(user, data, user_login)

        if user is not None:
            user_device: UserDevice | None = await self.get_entity_by_filters(
                UserDevice,
                [
                    UserDevice.device_id == device.id,
                    UserDevice.user_id == user.id,
                ],
                is_raise_exception=False,
            )
            if not user_device:
                user_device_service = self.get_service(c.MODULE_CODE_USER_DEVICES)
                await user_device_service.create(UserDeviceCreateRequest(user_id=user.id, device_id=device.id))

        self.entity_create_additional_fields["device_id"] = device.id
        self.entity_create_additional_fields["code"] = generate_password(
            get_password_characters("digits"), self.settings.backend_user_confirmation_code_length
        )

        filters = [
            self.model_class.device_id == device.id,
            getattr(self.model_class, user_login.field) == user_login.value,
        ]

        orders = [desc(self.model_class.created_on)]
        last_code = await self.get_entity_by_filters(self.model_class, filters, is_raise_exception=False, orders=orders)
        logger.debug(f"last_code={repr(await last_code.as_dict() if last_code else None)}")

        if last_code is None or last_code.group_number is None:
            self.entity_create_additional_fields["group_number"] = 1
            return None

        interval = (dt - last_code.created_on).total_seconds()
        logger.debug(f"interval={interval}")

        # Интервал > api_user_confirmation_code_limit_timeout - очистить все группы
        if interval > self.settings.backend_user_confirmation_code_limit_timeout.total_seconds():
            statement = (
                update(self.model_class)
                .where(*filters)
                .where(self.model_class.group_number.isnot(None))
                .values(group_number=None)
            )
            await self.session.execute(statement)
            logger.debug(
                f"interval={interval}, limit_timeout={self.settings.backend_user_confirmation_code_limit_timeout}"
            )
            return None

        # Интервал < 120 с
        if interval < self.settings.backend_user_confirmation_code_limit_same_group_attempts_timeout:
            logger.debug(
                f"interval={interval}, "
                f"limit_same_group_attempts_timeout="
                f"{self.settings.backend_user_confirmation_code_limit_same_group_attempts_timeout}"
            )
            seconds = round(self.settings.backend_user_confirmation_code_limit_same_group_attempts_timeout - interval)
            raise ConflictException(
                code="confirmation_code_limit_timeout",
                message_context={"login_title": user_login.title, "seconds": seconds},
                context={"seconds": seconds},
            )

        # Получить количество SMS в последней группе
        statement = (
            select(func.count(self.model_class.id))
            .where(*filters)
            .where(self.model_class.group_number == last_code.group_number)
        )
        statement_result = await self.session.execute(statement)
        group_codes_count = statement_result.scalar()
        logger.debug(f"group_codes_count={group_codes_count}")

        # 120 с < Интервал < 600 с
        if (
            self.settings.backend_user_confirmation_code_limit_same_group_attempts_timeout
            < interval
            < self.settings.backend_user_confirmation_code_limit_group_timeout
        ):
            logger.debug(
                f"interval={interval}, "
                f"limit_same_group_attempts_timeout="
                f"{self.settings.backend_user_confirmation_code_limit_same_group_attempts_timeout}, "
                f"limit_group_timeout={self.settings.backend_user_confirmation_code_limit_group_timeout}"
            )

            # Количество кодов в последней группе < 3
            if group_codes_count < self.settings.backend_user_confirmation_code_limit_same_group_attempts:
                logger.debug(
                    f"group_codes_count={group_codes_count}, "
                    f"limit_same_group_attempts={self.settings.backend_user_confirmation_code_limit_same_group_attempts}"
                )
                self.entity_create_additional_fields["group_number"] = last_code.group_number
                return None
            else:
                logger.debug(
                    f"group_codes_count={group_codes_count}, "
                    f"limit_same_group_attempts={self.settings.backend_user_confirmation_code_limit_same_group_attempts}"
                )
                seconds = round(self.settings.backend_user_confirmation_code_limit_group_timeout - interval)
                raise ConflictException(
                    code="confirmation_code_limit_timeout",
                    message_context={"login_title": user_login.title, "seconds": seconds},
                    context={"seconds": seconds},
                )

        # 600 с < Интервал < 24 ч
        if (
            self.settings.backend_user_confirmation_code_limit_group_timeout
            < interval
            < self.settings.backend_user_confirmation_code_limit_timeout.total_seconds()
        ):
            logger.debug(
                f"interval={interval}, "
                f"limit_group_timeout={self.settings.backend_user_confirmation_code_limit_group_timeout}, "
                f"limit_timeout={self.settings.backend_user_confirmation_code_limit_timeout}"
            )
            if group_codes_count < self.settings.backend_user_confirmation_code_limit_same_group_attempts:
                # Количество кодов в последней группе < 3
                logger.debug(
                    f"group_codes_count={group_codes_count}, "
                    f"limit_same_group_attempts={self.settings.backend_user_confirmation_code_limit_same_group_attempts}"
                )
                self.entity_create_additional_fields["group_number"] = last_code.group_number
                return None
            elif last_code.group_number < self.settings.backend_user_confirmation_code_limit_group_count:
                # Количество групп < 3
                logger.debug(
                    f"group_number={last_code.group_number}, "
                    f"limit_group_count={self.settings.backend_user_confirmation_code_limit_group_count}"
                )
                self.entity_create_additional_fields["group_number"] = last_code.group_number + 1
                return None
            else:
                logger.debug(
                    f"group_number={last_code.group_number}, "
                    f"limit_group_count={self.settings.backend_user_confirmation_code_limit_group_count}"
                )
                seconds = round(self.settings.backend_user_confirmation_code_limit_timeout.total_seconds() - interval)
                raise ConflictException(
                    code="confirmation_code_limit_timeout",
                    message_context={"login_title": user_login.title, "seconds": seconds},
                    context={"seconds": seconds},
                )

        return None

    async def after_entity_create(self, entity: UserAuthorizationCode, data: UserAuthorizationCodeRequest):
        """Выполнение дополнительных действия после создания объекта"""
        await self.session.execute(
            update(self.model_class)
            .where(
                self.model_class.id != entity.id,
                self.model_class.device_id == entity.device_id,
                self.model_class.email == entity.email if entity.email else self.model_class.phone == entity.phone,
                self.model_class.status == self.model_status_class.created,
            )
            .values(status=self.model_status_class.canceled, updated_on=entity.created_on, updated_by=entity.created_by)
        )

        # Отправляем код на email или в SMS
        # if entity.email:
        await self.send_email(self.template_event_code, getattr(entity, "user_id", None), entity.email, entity)
        # else:
        #     await self.send_sms(self.template_event_code, getattr(entity, "user_id", None), entity.phone, entity)

    async def ignore_codes(self, data: UserConfirmationCodeIgnoreRequest) -> dict:
        """Игнорирование кодов подтверждения"""
        await self.session.execute(
            update(self.model_class)
            .where(
                self.model_class.email == data.email if data.email else self.model_class.phone == data.phone,
                self.model_class.group_number.isnot(None),
            )
            .values(group_number=None)
        )
        await self.commit_and_refresh_entity()
        return {"is_ignored": True}

    def get_user_confirmation_code_response(
        self, entity: UserAuthorizationCodeModel | UserRegistrationCodeModel, time_zone: TimeZoneName
    ) -> UserConfirmationCodeResponse:
        """Получение схемы ответа на запрос получения кода подтверждения"""
        return UserConfirmationCodeResponse(
            confirmation_code_lifetime=get_datetime_as_timezone(
                entity.created_on + timedelta(seconds=self.settings.backend_user_confirmation_code_lifetime), time_zone
            ),
            confirmation_code_next_attempt_timeout=getattr(
                self.settings, "backend_user_confirmation_code_limit_same_group_attempts_timeout"
            ),
        )
