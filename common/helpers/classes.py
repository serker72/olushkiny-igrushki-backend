import inspect
from typing import Type


class BaseObject:
    """Базовый класс объекта"""

    def __init__(self, **kwargs):
        """Конструктор класса"""
        self.__dict__.update(kwargs)


class ACSCheckAction(BaseObject):
    """Класс проверки доступности действия"""

    actions: list[str]
    is_owner: bool = False

    def check_permit_actions(self, permit_actions: list[bool]) -> bool:
        """Проверка списка доступности действия"""
        return permit_actions[0]

    def check(self, available_actions: list[str]) -> bool:
        """Проверка доступности списка действий"""
        return self.check_permit_actions([action in available_actions for action in self.actions])


class ACSCheckActionAll(ACSCheckAction):
    """Класс проверки доступности всех действий из списка"""

    def check_permit_actions(self, permit_actions: list[bool]) -> bool:
        """Проверка списка доступности каждого действия"""
        return all(permit_actions)


class ACSCheckActionAny(ACSCheckAction):
    """Класс проверки доступности одного действия из списка"""

    def check_permit_actions(self, permit_actions: list[bool]) -> bool:
        """Проверка списка доступности каждого действия"""
        return any(permit_actions)


def get_class_properties(cls: Type) -> list:
    """Получение списка свойств класса"""
    return [i[0] for i in inspect.getmembers(cls) if not i[0].startswith("_") and not callable(i[1])]


def set_instance_attribute_values(instance: object, values: dict):
    """Установка значений атрибутов объекта на основании словаря"""
    for k, v in values.items():
        if hasattr(instance, k):
            setattr(instance, k, v)


ACSCheckActionTypes = (ACSCheckAction, ACSCheckActionAll, ACSCheckActionAny)
ACSCheckActionType = ACSCheckAction | ACSCheckActionAll | ACSCheckActionAny
ACSActionType = str | ACSCheckAction | ACSCheckActionAll | ACSCheckActionAny
