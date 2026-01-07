from enum import StrEnum


class UserRegistrationCodeStatuses(StrEnum):
    created = "Создан"
    confirmed = "Подтвержден"
    completed = "Зарегистрирован"
    canceled = "Отменен"


class UserAuthorizationCodeStatuses(StrEnum):
    created = "Создан"
    confirmed = "Подтвержден"
    canceled = "Отменен"
