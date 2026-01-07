import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from uuid import UUID

import isodate
from pydantic import BaseModel
from sqlalchemy_utils import Ltree


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return isodate.datetime_isoformat(obj)

        elif isinstance(obj, date):
            return isodate.date_isoformat(obj)

        elif isinstance(obj, time):
            return isodate.time_isoformat(obj)

        elif isinstance(obj, timedelta):
            return isodate.duration_isoformat(obj)

        elif isinstance(obj, Decimal):
            return float(obj)

        elif isinstance(obj, set):
            return list(obj)

        elif isinstance(obj, BaseModel):
            return obj.model_dump()

        elif isinstance(obj, Enum):
            return obj.value

        elif is_dataclass(obj) and not isinstance(obj, type):
            return {key: self.default(value) for key, value in asdict(obj).items()}

        elif isinstance(obj, UUID):
            return str(obj)

        elif isinstance(obj, bytes):
            return obj.decode()

        elif isinstance(obj, Ltree):
            return str(obj)

        return json.JSONEncoder.default(self, obj)


def custom_json_serializer(obj):
    return json.dumps(obj, cls=CustomJsonEncoder)


def dumps(obj, *args, **kwargs):
    if kwargs.get("cls") is None:
        kwargs["cls"] = CustomJsonEncoder

    return json.dumps(obj, *args, **kwargs)


def loads(obj, *args, **kwargs):
    return json.loads(obj, *args, **kwargs)
