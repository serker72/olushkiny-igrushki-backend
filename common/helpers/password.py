import hashlib
import hmac
import re
import string
from random import choices

from common.helpers import constants as c


def get_password_hash(password: str, password_salt: str, password_secret_key: str) -> str:
    """
    Получить хеш пароля.

    Алгоритм построения хеша пароля:

    - значение параметра `password_salt` делиться пополам - first_part, second_part
    - формируется строка `mixed_password` для хеширования - `{first_part}{password}{second_part}`
    - генерируется хеш строки - `hmac.new(password_secret_key, mixed_password, hashlib.sha512)`
    """
    part_length = len(password_salt) // 2
    first_part, second_part = password_salt[:part_length], password_salt[part_length:]
    mixed_password = f"{first_part}{password}{second_part}"
    return hmac.new(password_secret_key.encode("utf-8"), mixed_password.encode("utf-8"), hashlib.sha512).hexdigest()


def verify_password(password: str, password_salt: str, password_secret_key: str, password_hash: str | bytes) -> bool:
    """Проверить правильность пароля"""
    return get_password_hash(password, password_salt, password_secret_key) == (
        password_hash.decode("utf-8") if isinstance(password_hash, bytes) else password_hash
    )


def is_password_hash(password: str) -> bool:
    """Проверка наличия в строке хеша пароля"""
    return re.match(r"^[0-9a-fA-F]{64}$", password) is not None


def get_password_composition_regexp(characters: str, min_length: int) -> str:
    """Получение регулярного выражения для проверки пароля пользователя"""
    password_compositions = {
        c.PASSWORD_COMPOSITION_ASCII_LOWERCASE: "a-z",
        c.PASSWORD_COMPOSITION_ASCII_UPPERCASE: "A-Z",
        c.PASSWORD_COMPOSITION_DIGITS: "\\d",
        c.PASSWORD_COMPOSITION_PUNCTUATION: re.escape("!@#$%^&*()_-+=[\\]{}|;:',.<>/"),
    }
    allowed_categories = [category for category in characters.split(",") if category in password_compositions]
    regexp_length = f"{{{min_length},}}"

    letter_character_class = "".join(
        password_compositions[category]
        for category in (c.PASSWORD_COMPOSITION_ASCII_LOWERCASE, c.PASSWORD_COMPOSITION_ASCII_UPPERCASE)
        if category in allowed_categories
    )

    digit_and_punctuation_class = "".join(
        password_compositions[category]
        for category in (c.PASSWORD_COMPOSITION_DIGITS, c.PASSWORD_COMPOSITION_PUNCTUATION)
        if category in allowed_categories
    )

    lookahead_groups = ""
    if letter_character_class:
        lookahead_groups += f"(?=.*[{letter_character_class}])"
    if digit_and_punctuation_class:
        lookahead_groups += f"(?=.*[{digit_and_punctuation_class}])"

    allowed_symbols_class = "".join(password_compositions[category] for category in allowed_categories)

    if allowed_symbols_class:
        return f"^{lookahead_groups}[{allowed_symbols_class}]{regexp_length}$"
    else:
        return f"^.{regexp_length}$"


def validate_password(password: str, characters: str, min_length: int) -> bool:
    """Валидация пароля"""
    regexp = get_password_composition_regexp(characters, min_length)
    return re.match(regexp, password) is not None


def get_password_characters(characters: str) -> list[str]:
    """Получение списка символов для генерации пароля пользователя"""
    password_characters = {
        c.PASSWORD_COMPOSITION_ASCII_LOWERCASE: getattr(string, c.PASSWORD_COMPOSITION_ASCII_LOWERCASE),
        c.PASSWORD_COMPOSITION_ASCII_UPPERCASE: getattr(string, c.PASSWORD_COMPOSITION_ASCII_UPPERCASE),
        c.PASSWORD_COMPOSITION_DIGITS: getattr(string, c.PASSWORD_COMPOSITION_DIGITS),
        c.PASSWORD_COMPOSITION_PUNCTUATION: "!@#$%^&*()_-+=[\\]{}|;:',.<>/",
    }
    return [
        password_characters[category] for category in characters.split(",") if category in password_characters.keys()
    ]


def generate_password(password_characters: list[str], password_length: int) -> str:
    """Генерация пароля пользователя."""
    return "".join(choices("".join(password_characters), k=password_length))
