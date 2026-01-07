from collections import namedtuple
from datetime import date, datetime

import pytz

from common.helpers import constants as c


def normalize_seconds(seconds: int) -> tuple:
    """Получение количества дней, часов, минут, секунд из количества секунд"""
    (days, remainder) = divmod(seconds, 86400)
    (hours, remainder) = divmod(remainder, 3600)
    (minutes, seconds) = divmod(remainder, 60)

    return namedtuple("_", ("days", "hours", "minutes", "seconds"))(days, hours, minutes, seconds)


def get_datetime_as_default_timezone(dt: datetime) -> datetime:
    """Получение значения времени в часовом поясе по умолчанию"""
    default_timezone = pytz.timezone("Europe/Moscow")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.utc)

    return dt.astimezone(default_timezone)


def format_datetime_as_default_timezone(dt: datetime, dt_format: str = c.FORMAT_DATE_TIME) -> str:
    """Получение значения времени в часовом поясе по умолчанию в виде строки"""
    return get_datetime_as_default_timezone(dt).strftime(dt_format)


def format_date(d: date, dt_format: str = c.FORMAT_DATE) -> str:
    """Получение значения даты в виде строки"""
    return d.strftime(dt_format)


def format_datetime(dt: datetime):
    return format_datetime_as_default_timezone(dt) + " (МСК)"


def get_datetime_as_timezone(dt: datetime, time_zone: str) -> datetime:
    """Получение значения времени в указанном часовом поясе"""
    if time_zone not in pytz.all_timezones:
        return dt

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.utc)

    return dt.astimezone(pytz.timezone(time_zone))


def get_dict_datetime_as_timezone(d: dict, time_zone: str) -> datetime:
    """Получение значений времени в словаре в указанном часовом поясе"""
    data = {}
    for key, value in d.items():
        if isinstance(value, datetime):
            data[key] = get_datetime_as_timezone(value, time_zone)
        elif isinstance(value, dict):
            data[key] = get_dict_datetime_as_timezone(value, time_zone)
        elif isinstance(value, list):
            data[key] = [
                get_datetime_as_timezone(item, time_zone)
                if isinstance(item, datetime)
                else (get_dict_datetime_as_timezone(item, time_zone) if isinstance(item, dict) else item)
                for item in value
            ]
        else:
            data[key] = value

    return data
