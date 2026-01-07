import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP, SMTPRecipientsRefused, SMTPResponseException
from typing import Iterable, Tuple

from common.helpers.exception import get_traceback
from common.schemas.models import BackendSettings


def check_email(email: str) -> bool:
    """Проверка адреса с учетом национальных доменов"""

    email = email.lower().strip()

    username_valid_chars = r"[0-9a-zа-я._+-]"
    domain_valid_chars = r"[0-9a-zа-я.-]"

    try:
        username, domain = email.split("@")

        username_check = len(re.sub(username_valid_chars, "", username)) == 0
        domain_check = len(re.sub(domain_valid_chars, "", domain)) == 0
        return username_check and domain_check
    except ValueError:
        return False


def send_email(
    *, subject: str, body: str, to: Iterable[str], settings: BackendSettings
) -> Tuple[bool, dict | None, int | None, str | None]:
    """Универсальная отправка email через SMTP"""
    try:
        message = MIMEMultipart("alternative")
        message["From"] = settings.smtp_mail_from
        message["Subject"] = subject
        message["To"] = ",".join(to)
        message.attach(MIMEText(body, "html", "utf-8"))

        smtp_client = SMTP(host=settings.smtp_host, port=settings.smtp_port, timeout=settings.smtp_timeout)
        smtp_client.connect(host=settings.smtp_host, port=settings.smtp_port)

        if settings.smtp_starttls is True:
            smtp_client.starttls()

        smtp_client.login(user=settings.smtp_user, password=settings.smtp_password)
        smtp_result = smtp_client.send_message(message)
        smtp_client.quit()

        ok = not bool(smtp_result)
        return ok, smtp_result, None, None

    except Exception as e:
        if isinstance(e, SMTPResponseException):
            smtp_code = e.smtp_code
        elif isinstance(e, SMTPRecipientsRefused):
            smtp_code = 550
        else:
            smtp_code = None
        return False, None, smtp_code, get_traceback(e)
