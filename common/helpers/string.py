import re
from typing import Annotated, Any

from pydantic import ValidationInfo, ValidatorFunctionWrapHandler, WrapValidator


def to_camel_case(snake_case_str, as_list: bool = False) -> str | list[str]:
    """Преобразование строки из формата snake_case в формат CamelCase"""
    parts = [x.capitalize() for x in snake_case_str.lower().split("_")]
    return parts if as_list is True else "".join(parts)


def to_lower_camel_case(snake_str, as_list: bool = False) -> str | list[str]:
    """Преобразование строки из формата snake_case в формат camelCase"""
    parts = to_camel_case(snake_str, True)
    parts[0] = parts[0].lower()
    return parts if as_list is True else "".join(parts)


def to_snake_case(camel_case_str, as_list: bool = False) -> str | list[str]:
    """Преобразование строки из формата camelCase/CamelCase в формат snake_case"""
    if camel_case_str[0].islower():
        camel_case_str = camel_case_str[0].upper() + camel_case_str[1:]

    parts = [s.lower() for s in re.sub(r"([A-Z])", r" \1", camel_case_str).split()]
    return parts if as_list is True else "_".join(parts)


def string_masked(s: str, visible_digits: int, mask_position: str, mask_symbol: str = "*") -> str:
    """Маскировка строки"""
    length = len(s)
    mask_length = length - visible_digits
    if mask_position == "left":
        return mask_symbol * mask_length + s[-visible_digits:]
    elif mask_position == "right":
        return s[:visible_digits] + mask_symbol * mask_length
    else:
        visible_digits_left = visible_digits // 2
        visible_digits_right = visible_digits - visible_digits_left
        return s[:visible_digits_left] + mask_symbol * mask_length + s[-visible_digits_right:]


def string_clear_space(s: str) -> str:
    """Очистка строки от пробелов"""
    return re.sub(" +", " ", s)


def string_replace_space(s: str, symbol: str = "_") -> str:
    """Замена в строке пробелов на указанный символ"""
    return s.replace(" ", symbol)


def name_singular_to_plural(name: str) -> str:
    """Преобразование имени из единственного числа во множественное"""
    return f"{name[:-1]}ies" if name[-1] == "y" else f"{name}s"


def name_plural_to_singular(name: str) -> str:
    """Преобразование имени из множественного числа в единственное"""
    return f"{name[:-3]}y" if name.endswith("ies") else name[:-1]


def get_file_name_from_url(url: str) -> str:
    """Получение имени файла из URL"""
    return url.split("/")[-1].split("?")[0]


def maybe_list_of_strings(v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> list[str]:
    if isinstance(v, str):
        return v.split(",")

    return v


CustomListOfStrings = Annotated[list, WrapValidator(maybe_list_of_strings)]
