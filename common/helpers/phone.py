from contextlib import suppress

import phonenumbers as pn


def verify_user_phone(phone: str) -> str | None:
    """Проверить номер телефона пользователя"""
    with suppress(pn.phonenumberutil.NumberParseException):
        z = pn.parse(phone, None)
        if pn.is_possible_number(z) and pn.is_valid_number(z):
            return pn.format_number(z, pn.PhoneNumberFormat.E164)

    return None
