from starlette_wtf import StarletteForm
from wtforms import SelectField, StringField
from wtforms.validators import DataRequired

from common.helpers import constants as c


class CategoryCreateForm(StarletteForm):
    name = StringField(
        "Наименование",
        render_kw={
            "class": "form-control",
            "placeholder": "Введите наименование",
        },
        validators=[DataRequired(message=c.FORM_FIELD_REQUIRED_MESSAGE)],
    )
    sku_prefix = StringField(
        "Префикс артикула",
        render_kw={
            "class": "form-control",
            "placeholder": "Введите префикс артикула",
        },
        validators=[DataRequired(message=c.FORM_FIELD_REQUIRED_MESSAGE)],
    )


class CategoryUpdateForm(CategoryCreateForm):
    state_id = SelectField(
        "Статус",
        coerce=int,
        render_kw={
            "class": "form-control",
        },
        validators=[DataRequired(message=c.FORM_FIELD_REQUIRED_MESSAGE)],
    )
