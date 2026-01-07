import asyncio
import traceback
from abc import ABC, abstractmethod
from typing import TypeVar

from aio_pika import ExchangeType, connect_robust
from aio_pika.abc import AbstractIncomingMessage, AbstractRobustChannel
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app_backend.services.base import ServiceManager
from common.helpers import json
from common.helpers.database import get_sa_async_session
from common.helpers.lock import task_lock
from common.schemas.models.settings import BackendSettings


class BaseWorkerRMQ(ABC):
    """Класс базового обработчика сообщений в очереди RabbitMQ"""

    rmq_channel: AbstractRobustChannel = None
    settings: BackendSettings = None
    service_manager: ServiceManager = None
    worker_id: int = None
    queue_name: str = None
    reconnect_timeout: int = 2
    consume_method_is_lock: bool = False
    consume_method_lock_ttl: int = 60
    consume_method_lock_is_delete: bool = False
    message_delay_time: int = 0

    def __init__(self, **kwargs):
        """Конструктор класса"""
        self.__dict__.update(kwargs)

    async def before_run(self):
        """Действия перед запуском обработчика"""

    async def run(self):
        """Запуск обработчика"""
        logger.info(f"queue_name: {self.queue_name}, worker_id: {self.worker_id}")

        await self.before_run()

        try:
            rmq_connection = await connect_robust(self.settings.get_rabbitmq_url(), loop=asyncio.get_running_loop())
        except Exception as e:
            logger.error(e)
            await asyncio.sleep(self.reconnect_timeout)
            return await self.run()

        async with rmq_connection:
            self.rmq_channel = await rmq_connection.channel()

            rmq_exchange = await self.rmq_channel.declare_exchange(
                f"{self.queue_name}.exchange",
                "x-delayed-message" if self.message_delay_time else ExchangeType.DIRECT,
                durable=True,
                # auto_delete=True,
                arguments={"x-delayed-type": "direct"} if self.message_delay_time else None,
            )

            rmq_queue = await self.rmq_channel.declare_queue(
                self.queue_name,
                durable=True,
                # auto_delete=True,
            )

            await rmq_queue.bind(rmq_exchange, self.queue_name)

            await rmq_queue.consume(self.on_message_pre_processing, no_ack=False)

            try:
                await asyncio.Future()
            except Exception as e:
                logger.error(e)
                await asyncio.sleep(self.reconnect_timeout)
                return await self.run()

    def get_lock_key(self, data: dict) -> str:
        """Получение ключа блокировки"""
        return self.queue_name

    async def on_message_pre_processing(self, message: AbstractIncomingMessage):
        """Предварительная обработка сообщения из очереди"""
        with logger.contextualize(p_id=message.message_id):
            data = json.loads(message.body.decode())
            logger.info(f"Message body: {repr(data)}")

            @task_lock(
                lock_key=self.get_lock_key(data),
                ttl=self.consume_method_lock_ttl,
                is_delete=self.consume_method_lock_is_delete,
            )
            async def get_is_locked() -> bool:
                """Получение флага успешной установки блокировки"""
                # logger.debug(f"data: {repr(data)}")
                return True

            is_locked = await get_is_locked() if self.consume_method_is_lock else False
            logger.info(f"consume_method_is_lock={self.consume_method_is_lock}, is_locked={is_locked}")
            try:
                await self.on_message_processing(message.message_id, data, is_locked)
                await message.ack()
            except Exception:
                logger.error(f"Worker error: {traceback.format_exc()}")
                await message.nack(requeue=True)
                raise

    @abstractmethod
    async def on_message_processing(self, message_id: str, data: dict, is_locked: bool):
        """Обработка сообщения из очереди"""


class BaseSAWorkerRMQ(BaseWorkerRMQ, ABC):
    """Класс базового обработчика сообщений в очереди RabbitMQ с использованием сессии SQLAlchemy"""

    engine: AsyncEngine = None
    session: AsyncSession = None

    async def on_message_processing(self, message_id: str, data: dict, is_locked: bool):
        """Обработка сообщения из очереди"""
        async with get_sa_async_session(self.engine) as self.session:
            await self.on_message_sa_processing(message_id, data, is_locked)

    @abstractmethod
    async def on_message_sa_processing(self, message_id: str, data: dict, is_locked: bool):
        """Обработка сообщения из очереди с использованием сессии SQLAlchemy"""


BaseWorkerRMQType = TypeVar("BaseWorkerRMQType", bound=BaseWorkerRMQ)
