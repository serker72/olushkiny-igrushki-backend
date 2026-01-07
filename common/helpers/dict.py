import json
from contextlib import suppress
from decimal import Decimal
from functools import reduce
from operator import getitem
from pathlib import Path
from typing import Any

from pydantic import ValidationInfo, ValidatorFunctionWrapHandler
from tomlkit_extras import load_toml_file

# from common.exceptions import UnprocessableEntityException
from common.helpers.file import check_file_exists, get_file_content


def maybe_dict(v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> dict:
    if isinstance(v, str):
        try:
            return json.loads(v)
        except (TypeError, json.JSONDecoder):
            # raise UnprocessableEntityException(code="json_structure_is_invalid")
            raise ValueError("json_structure_is_invalid")

    return v


def maybe_dict_from_file(v: Any) -> dict:
    if isinstance(v, str):
        if not v.startswith("{"):
            if not check_file_exists(v):
                # raise UnprocessableEntityException(code="file_name_not_exists", message_context={"name": v})
                raise FileNotFoundError(v)

            v = get_file_content(v)

        try:
            return json.loads(v)
        except (TypeError, json.JSONDecodeError):
            # raise UnprocessableEntityException(code="json_structure_is_invalid")
            raise ValueError(code="json_structure_is_invalid")

    return v


def object_to_dict(obj: object, ignored_attributes: list[str] = None) -> dict:
    """Преобразование экземпляра класса в словарь"""
    ignored_attributes = ignored_attributes or []
    data = {}
    attributes = [
        attribute
        for attribute in dir(obj)
        if not attribute.startswith("__") and not attribute.startswith("_") and attribute not in ignored_attributes
    ]
    for attr in attributes:
        value = getattr(obj, attr)

        if hasattr(value, "__dict__"):
            data[attr] = object_to_dict(value, ignored_attributes)
        elif isinstance(value, Decimal):
            data[attr] = float(value)
        else:
            data[attr] = value

    return data


def get_dict_item_by_path(d: dict, keys: list[str]) -> Any | None:
    """Получение элемента вложенного словаря по списку ключей"""
    with suppress(Exception):
        return reduce(getitem, keys, d)


def set_dict_item_by_path(d: dict, keys: list[str], value: Any):
    """Установка значения элемента вложенного словаря по списку ключей"""
    for index in range(1, len(keys)):
        sub_item = get_dict_item_by_path(d, keys[:index])
        if not isinstance(sub_item, dict):
            get_dict_item_by_path(d, keys[:index][:-1])[keys[:index][-1]] = {}

    get_dict_item_by_path(d, keys[:-1])[keys[-1]] = value


def get_dict_from_toml_file(file_name: str | Path, keys: list[str] | dict[str, str] = None) -> dict:
    """
    Получение словаря из файла TOML с опционально ограниченным списком ключей.

    Опциональный параметр `keys` может содержать:
    - список получаемых ключей - ["key1", "key2.key3"]
    - словарь получаемых ключей - {"in_key1": "out_key1", "in_key2.in_key3": "out_key2.out_key3"}
    """
    if not check_file_exists(file_name):
        from common.exceptions import ServerErrorException

        raise ServerErrorException(code="file_name_not_exists", message_context={"name": file_name})

    toml_doc = load_toml_file(file_name)
    toml_dict = toml_doc.unwrap()

    if keys is None or len(keys) == 0:
        return toml_dict

    keys = {key: key for key in keys} if not isinstance(keys, dict) else keys

    data = {}
    for in_key, out_key in keys.items():
        set_dict_item_by_path(data, out_key.split("."), get_dict_item_by_path(toml_dict, in_key.split(".")))

    return data


def get_dict_items(d: dict, include_keys: list[str | int] = None, exclude_keys: list[str] = None) -> dict:
    """Получение элемента вложенного словаря по списку ключей"""
    include_keys = include_keys or []
    exclude_keys = exclude_keys or []
    data = {}
    for key, value in d.items():
        if key not in exclude_keys and (len(include_keys) == 0 or key in include_keys):
            data[key] = value

    return data
