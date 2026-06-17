from starlette_wtf import StarletteForm
from wtforms import SelectField, StringField
from wtforms.validators import AnyOf, DataRequired

from common.helpers import constants as c


class PropertyCreateForm(StarletteForm):
    """Класс формы создания свойства объекта модуля"""

    module_id = SelectField(
        "Модуль",
        coerce=int,
        render_kw={
            "class": "form-control",
        },
        validators=[DataRequired(message=c.FORM_FIELD_REQUIRED_MESSAGE)],
    )
    name = StringField(
        "Наименование",
        render_kw={
            "class": "form-control",
            "placeholder": "Введите наименование",
        },
        validators=[DataRequired(message=c.FORM_FIELD_REQUIRED_MESSAGE)],
    )
    is_required = SelectField(
        "Флаг обязательности",
        coerce=int,
        render_kw={
            "class": "form-control",
        },
        validators=[DataRequired(message=c.FORM_FIELD_REQUIRED_MESSAGE)],
    )


class PropertyUpdateForm(PropertyCreateForm):
    """Класс формы создания свойства объекта модуля"""

    is_active = SelectField(
        "Флаг активности",
        coerce=int,
        render_kw={
            "class": "form-control",
        },
        validators=[AnyOf(values=[0, 1], message=c.FORM_FIELD_REQUIRED_MESSAGE)],
    )
