from loguru import logger
from sqlalchemy import update

from app_queue_processing.workers import BaseSAWorkerRMQ
from common.helpers import json, timeutil
from common.helpers.email import send_email
from common.helpers.exception import get_traceback
from common.models import EmailMessage


class EmailMessageWorkerRMQ(BaseSAWorkerRMQ):
    """Класс обработчика сообщений в очереди RabbitMQ, созданных на основании записей в таблице `email_messages`"""

    async def on_message_sa_processing(self, message_id: str, data: dict, is_locked: bool):
        """Обработка сообщения из очереди с использованием сессии SQLAlchemy"""
        # Список кодов ошибок, для которых повторные попытки отправки не выполняются
        not_retry_smtp_codes = [
            535,  # AuthenticationError
            550,  # BrandUser unknown
            554,  # InvalidRecipientsException
        ]

        result = {
            "is_sent": False,
            "is_error": None,
            "sending_errors": {},
            "repeated_attempts": 0,
        }

        for attempt in range(1, self.settings.smtp_retry_limit + 1):
            logger.info(f"Send message to email {data['user_email']}, attempt {attempt}")
            try:
                ok, smtp_result, smtp_code, error_text = send_email(
                    subject=data["subject"],
                    body=data["body"],
                    to=[data["user_email"]],
                    settings=self.settings,
                )
                logger.info(f"smtp_result: {repr(smtp_result)} smtp_code={smtp_code} ok={ok}")

                if ok:
                    result["is_sent"] = True
                    break

                result["is_error"] = True
                result["repeated_attempts"] = attempt - 1
                result["sending_errors"][f"attempt-{attempt}"] = error_text or f"smtp_result={repr(smtp_result)}"

                if smtp_code in not_retry_smtp_codes:
                    break

            except Exception as e:
                trace = get_traceback(e)
                logger.error(trace)

                result["is_error"] = True
                result["repeated_attempts"] = attempt - 1
                result["sending_errors"][f"attempt-{attempt}"] = getattr(
                    e, "smtp_error", getattr(e, "msg", None)
                ) or str(e)

        statement = (
            update(EmailMessage)
            .where(EmailMessage.id == message_id)
            .values(
                is_sent=result["is_sent"],
                is_error=result["is_error"],
                sending_errors=json.dumps(result["sending_errors"]) if len(result["sending_errors"]) else None,
                repeated_attempts=result["repeated_attempts"],
                updated_on=timeutil.utcnow(),
            )
        )
        await self.session.execute(statement)
        await self.session.flush()
