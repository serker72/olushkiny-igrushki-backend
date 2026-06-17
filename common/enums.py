from enum import Enum, StrEnum


class ExtendedEnum(Enum):
    @classmethod
    def keys(cls):
        return list(map(lambda e: e.name, cls))

    @classmethod
    def values(cls):
        return list(map(lambda e: e.value, cls))

    @classmethod
    def to_dict(cls):
        return cls.mapping() if hasattr(cls, "mapping") else {item.name: item.value for item in iter(cls)}

    @classmethod
    def to_list_of_tuples(cls):
        return (
            [(k, v) for k, v in cls.mapping().items()]
            if hasattr(cls, "mapping")
            else [(item.name, item.value) for item in iter(cls)]
        )


class UserRegistrationCodeStatuses(StrEnum):
    created = "Создан"
    confirmed = "Подтвержден"
    completed = "Зарегистрирован"
    canceled = "Отменен"


class UserAuthorizationCodeStatuses(StrEnum):
    created = "Создан"
    confirmed = "Подтвержден"
    canceled = "Отменен"


class FlagStatus(ExtendedEnum):
    ENABLED = ("1", "Включен")
    DISABLED = ("0", "Выключен")
