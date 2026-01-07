from datetime import datetime, timezone

from common.helpers import constants as c


def utcnow():
    """Обычный datetime.utcnow() возвращает datetime-naive объект, у которого tzinfo=None
    Если это время записать в postgres и прочитать обратно, получится datetime-aware, у которого tzinfo=datetime.utc

    А такие объекты нельзя сравнивать между собой

    Отдельная функция нужна из-за sqlalchemy:
    updated_on = Column(DateTime, default=callable_func)
    Если сделать так: default=datetime.now(timezone.utc), то время станет константой
    """

    return datetime.now(timezone.utc)


def dt_to_str(dt: datetime, dt_format: str = None) -> str:
    """Преобразование времени в строку по указанному формату"""
    dt_format = dt_format or c.FORMAT_DATE_TIME
    return dt.strftime(dt_format)
