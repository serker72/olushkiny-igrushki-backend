from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, case, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from .base import AuditMixin, Base, BaseWithPhoto, BaseWithState
from .case import UserCase


class User(AuditMixin, BaseWithState, BaseWithPhoto, Base):
    case = UserCase
    relation_fields = {
        "state": "state",
        # "photo": "photo.url",
        "photo": "photo",
        # "roles": "roles",
    }
    media_fields = ["photo"]

    # state_id: Mapped[int] = mapped_column(ForeignKey("module_states.id", ondelete="CASCADE"))
    surname: Mapped[str] = mapped_column(String(), nullable=False)
    name: Mapped[str] = mapped_column(String(), nullable=False)
    second_name: Mapped[str] = mapped_column(String())
    email: Mapped[str] = mapped_column(String(), nullable=False)
    # password: Mapped[str] = mapped_column(String(), nullable=False)
    phone: Mapped[str] = mapped_column(String(), nullable=True)
    birthday: Mapped[date] = mapped_column(Date(), nullable=True)
    time_zone: Mapped[str] = mapped_column(String(), nullable=False, server_default="Europe/Moscow")
    last_logged_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    # incorrect_password_attempts: Mapped[int] = mapped_column(SmallInteger(), default=0, nullable=False)
    # incorrect_password_lockout_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # relations
    # state = relationship("ModuleState", viewonly=True, uselist=False, lazy="selectin")

    @hybrid_property
    def fio(self):
        return " ".join(
            [
                self.surname,
                f"{self.name.strip()[:1]}." if self.name and self.name.strip() else "",
                f"{self.second_name.strip()[:1]}." if self.second_name and self.second_name.strip() else "",
            ]
        ).strip()

    @fio.expression
    def fio(self):
        return func.rtrim(
            func.concat(
                self.surname,
                " ",
                case(
                    (
                        func.length(func.left(func.ltrim(self.name), 1)) == 1,
                        func.concat(func.left(func.ltrim(self.name), 1), "."),
                    ),
                    else_="",
                ),
                " ",
                case(
                    (
                        func.length(func.left(func.ltrim(self.second_name), 1)) == 1,
                        func.concat(func.left(func.ltrim(self.second_name), 1), "."),
                    ),
                    else_="",
                ),
            ),
        )

    @hybrid_property
    def full_name(self):
        return " ".join(
            [
                self.surname,
                self.name.strip() if self.name and self.name.strip() else "",
                self.second_name.strip() if self.second_name and self.second_name.strip() else "",
            ]
        ).strip()

    @full_name.expression
    def full_name(self):
        return func.rtrim(
            func.concat(
                self.surname,
                " ",
                case(
                    (
                        func.length(func.ltrim(self.name)) > 0,
                        func.ltrim(self.name),
                    ),
                    else_="",
                ),
                " ",
                case(
                    (
                        func.length(func.ltrim(self.second_name)) > 0,
                        func.ltrim(self.second_name),
                    ),
                    else_="",
                ),
            ),
        )

    # @hybrid_property
    # def remaining_password_attempts(self) -> int:
    #     """Количество оставшихся попыток ввода пароля"""
    #     return settings.api_user_incorrect_password_attempts - self.incorrect_password_attempts
