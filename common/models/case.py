from typing import Protocol


class Case(Protocol):
    nominative: str = "Объект"  # именительный падеж (кто, что?)
    genitive: str = "Объекта"  # родительный падеж (кого, чего?)
    dative: str = "Объекту"  # дательный падеж (кому, чему? 	)
    accusative: str = "Объект"  # винительный падеж (кого, что?)
    instrumental: str = "Объектом"  # творительный падеж (кем, чем?)
    prepositional: str = "Объекте"  # предложный падеж (о ком, о чём?)

    # множественное число
    plural_nominative: str = "Объекты"  # именительный падеж (кто, что?)
    plural_genitive: str = "Объектов"  # родительный падеж (кого, чего?)
    plural_dative: str = "Объектам"  # дательный падеж (кому, чему? 	)
    plural_accusative: str = "Объекты"  # винительный падеж (кого, что?)
    plural_instrumental: str = "Объектами"  # творительный падеж (кем, чем?)
    plural_prepositional: str = "Объектах"  # предложный падеж (о ком, о чём?)


class RoleCase(Case):
    nominative = "Роль"
    genitive = "Роли"
    dative = "Роли"
    accusative = "Роль"
    instrumental = "Ролью"
    prepositional = "Роли"

    plural_nominative = "Роли"
    plural_genitive = "Ролей"
    plural_dative = "Ролям"
    plural_accusative = "Роли"
    plural_instrumental = "Ролями"
    plural_prepositional = "Ролях"


class UserRoleCase(Case):
    nominative = "Роль пользователя"
    genitive = "Роли пользователя"
    dative = "Роли пользователя"
    accusative = "Роль пользователя"
    instrumental = "Ролью пользователя"
    prepositional = "Роли пользователя"

    plural_nominative = "Роли пользователя"
    plural_genitive = "Ролей пользователя"
    plural_dative = "Ролям пользователя"
    plural_accusative = "Роли пользователя"
    plural_instrumental = "Ролями пользователя"
    plural_prepositional = "Ролях пользователя"


class UserCase(Case):
    nominative = "Пользователь"
    genitive = "Пользователя"
    dative = "Пользователю"
    accusative = "Пользователя"
    instrumental = "Пользователем"
    prepositional = "Пользователе"

    plural_nominative = "Пользователи"
    plural_genitive = "Пользователей"
    plural_dative = "Пользователям"
    plural_accusative = "Пользователей"
    plural_instrumental = "Пользователями"
    plural_prepositional = "Пользователях"


class ModuleCase(Case):
    nominative = "Модуль"
    genitive = "Модуля"
    dative = "Модулю"
    accusative = "Модуль"
    instrumental = "Модулем"
    prepositional = "Модуле"

    plural_nominative = "Модули"
    plural_genitive = "Модулей"
    plural_dative = "Модулям"
    plural_accusative = "Модули"
    plural_instrumental = "Модулями"
    plural_prepositional = "Модулях"


class ModuleStateCase(Case):
    nominative = "Статус объектов модуля"
    genitive = "Статуса объектов модуля"
    dative = "Статусу объектов модуля"
    accusative = "Статус объектов модуля"
    instrumental = "Статусом объектов модуля"
    prepositional = "Статусе объектов модуля"

    plural_nominative = "Статусы объектов модулей"
    plural_genitive = "Статусов объектов модулей"
    plural_dative = "Статусам объектов модулей"
    plural_accusative = "Статусы объектов модулей"
    plural_instrumental = "Статусами объектов модулей"
    plural_prepositional = "Статусах объектов модулей"


class FileCase(Case):
    nominative = "Файл"
    genitive = "Файла"
    dative = "Файлу"
    accusative = "Файл"
    instrumental = "Файлом"
    prepositional = "Файле"

    plural_nominative = "Файлы"
    plural_genitive = "Файлов"
    plural_dative = "Файлам"
    plural_accusative = "Файлы"
    plural_instrumental = "Файлами"
    plural_prepositional = "Файлах"


class EmailMessageCase(Case):
    nominative = "Электронное сообщение"
    genitive = "Электронного сообщения"
    dative = "Электронному сообщению"
    accusative = "Электронное сообщение"
    instrumental = "Электронным сообщением"
    prepositional = "Электронном сообщении"

    plural_nominative = "Электронные сообщения"
    plural_genitive = "Электронных сообщений"
    plural_dative = "Электронным сообщениям"
    plural_accusative = "Электронные сообщения"
    plural_instrumental = "Электронными сообщениями"
    plural_prepositional = "Электронных сообщениях"


class ActionCase(Case):
    nominative = "Действие"
    genitive = "Действия"
    dative = "Действию"
    accusative = "Действие"
    instrumental = "Действием"
    prepositional = "Действии"

    plural_nominative = "Действия"
    plural_genitive = "Действий"
    plural_dative = "Действиям"
    plural_accusative = "Действия"
    plural_instrumental = "Действиями"
    plural_prepositional = "Действиях"


class ModuleActionCase(Case):
    nominative = "Действие модуля"
    genitive = "Действия модуля"
    dative = "Действию модуля"
    accusative = "Действие модуля"
    instrumental = "Действием модуля"
    prepositional = "Действии модуля"

    plural_nominative = "Действия модулей"
    plural_genitive = "Действий модулей"
    plural_dative = "Действиям модулей"
    plural_accusative = "Действия модулей"
    plural_instrumental = "Действиями модулей"
    plural_prepositional = "Действиях модулей"


class RoleModuleActionCase(Case):
    nominative = "Действие модуля, доступное для роли"
    genitive = "Действия модуля, доступного для роли"
    dative = "Действию модуля, доступному для роли"
    accusative = "Действие модуля, доступное для роли"
    instrumental = "Действием модуля, доступным для роли"
    prepositional = "Действии модуля, доступном для роли"

    plural_nominative = "Действия модулей, доступные для ролей"
    plural_genitive = "Действий модулей, доступных для ролей"
    plural_dative = "Действиям модулей, доступным для ролей"
    plural_accusative = "Действия модулей, доступные для ролей"
    plural_instrumental = "Действиями модулей, доступными для ролей"
    plural_prepositional = "Действиях модулей, доступных для ролей"


class ModuleEventsCase(Case):
    nominative = "Событие модуля"
    genitive = "События модуля"
    dative = "Событию модуля"
    accusative = "Событие модуля"
    instrumental = "Событием модуля"
    prepositional = "Событии модуля"

    plural_nominative = "События модулей"
    plural_genitive = "Событий модулей"
    plural_dative = "Событиям модулей"
    plural_accusative = "События модулей"
    plural_instrumental = "Событиями модулей"
    plural_prepositional = "Событиях модулей"


class DeviceCase(Case):
    nominative = "Устройство"
    genitive = "Устройства"
    dative = "Устройству"
    accusative = "Устройство"
    instrumental = "Устройством"
    prepositional = "Устройстве"

    plural_nominative = "Устройства"
    plural_genitive = "Устройств"
    plural_dative = "Устройствам"
    plural_accusative = "Устройства"
    plural_instrumental = "Устройствами"
    plural_prepositional = "Устройствах"


class UserDeviceCase(Case):
    nominative = "Связь пользователя с устройством"
    genitive = "Связи пользователя с устройством"
    dative = "Связи пользователя с устройством"
    accusative = "Связь пользователя с устройством"
    instrumental = "Связью пользователя с устройством"
    prepositional = "Связи пользователя с устройством"

    plural_nominative = "Связи пользователя с устройствами"
    plural_genitive = "Связей пользователя с устройствами"
    plural_dative = "Связям пользователя с устройствами"
    plural_accusative = "Связи пользователя с устройствами"
    plural_instrumental = "Связями пользователя с устройствами"
    plural_prepositional = "Связях пользователя с устройствами"


class UserRegistrationCodeCase(Case):
    nominative = "Код подтверждения регистрации"
    genitive = "Кода подтверждения регистрации"
    dative = "Коду подтверждения регистрации"
    accusative = "Код подтверждения регистрации"
    instrumental = "Кодом подтверждения регистрации"
    prepositional = "Коде подтверждения регистрации"

    plural_nominative = "Коды подтверждения регистрации"
    plural_genitive = "Кодов подтверждения регистрации"
    plural_dative = "Кодам подтверждения регистрации"
    plural_accusative = "Коды подтверждения регистрации"
    plural_instrumental = "Кодами подтверждения регистрации"
    plural_prepositional = "Кодах подтверждения регистрации"


class UserAuthorizationCodeCase(Case):
    nominative = "Код подтверждения авторизации"
    genitive = "Кода подтверждения авторизации"
    dative = "Коду подтверждения авторизации"
    accusative = "Код подтверждения авторизации"
    instrumental = "Кодом подтверждения авторизации"
    prepositional = "Коде подтверждения авторизации"

    plural_nominative = "Коды подтверждения авторизации"
    plural_genitive = "Кодов подтверждения авторизации"
    plural_dative = "Кодам подтверждения авторизации"
    plural_accusative = "Коды подтверждения авторизации"
    plural_instrumental = "Кодами подтверждения авторизации"
    plural_prepositional = "Кодах подтверждения авторизации"
