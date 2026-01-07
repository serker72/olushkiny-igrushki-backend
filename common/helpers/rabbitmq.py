import asyncio
from uuid import UUID, uuid4

from aio_pika import ExchangeType, Message, connect_robust
from loguru import logger
from pika import BasicProperties, BlockingConnection, ConnectionParameters, PlainCredentials
from pydantic import BaseModel

from common.helpers import json
from common.schemas.models.base import BaseModelType
from common.schemas.models.settings import settings


async def async_publish_message(
    app_id: str,
    queue_name: str,
    data: BaseModelType | dict,
    exchange_name: str | None = None,
    routing_key: str | None = None,
    delay_time: int | None = None,
    message_id: UUID | None = None,
):
    """Публикация сообщения в указанную очередь в асинхронном режиме"""
    message_id = message_id or str(uuid4().hex)
    exchange_name = exchange_name or f"{queue_name}.exchange"
    routing_key = routing_key or queue_name
    data = data.model_dump() if isinstance(data, BaseModel) else data
    if delay_time:
        data["delay"] = delay_time

    rmq_connection = await connect_robust(settings.get_rabbitmq_url(), loop=asyncio.get_running_loop())

    async with rmq_connection:
        rmq_channel = await rmq_connection.channel()

        rmq_exchange = await rmq_channel.declare_exchange(
            exchange_name,
            "x-delayed-message" if delay_time else ExchangeType.DIRECT,
            durable=True,
            # auto_delete=True,
            arguments={"x-delayed-type": "direct"} if delay_time else None,
        )

        rmq_queue = await rmq_channel.declare_queue(
            queue_name,
            durable=True,
            # auto_delete=True,
        )

        await rmq_queue.bind(rmq_exchange, queue_name)
        message = Message(
            body=json.dumps(data).encode(),
            app_id=app_id,
            headers={"x-delay": delay_time} if delay_time else None,
            message_id=message_id,
        )
        await rmq_exchange.publish(message, routing_key=routing_key)
        logger.info(
            f"exchange_name: {exchange_name}, queue_name: {queue_name}, routing_key: {routing_key}, "
            f"app_id: {message.app_id}, message_id: {message_id}, data: {repr(data)}"
        )


def publish_message(
    app_id: str,
    queue_name: str,
    data: BaseModelType | dict,
    exchange_name: str | None = None,
    routing_key: str | None = None,
    delay_time: int | None = None,
    message_id: UUID | None = None,
):
    """Публикация сообщения в указанную очередь"""
    message_id = message_id or str(uuid4().hex)
    exchange_name = exchange_name or f"{queue_name}.exchange"
    routing_key = routing_key or queue_name
    data = data.model_dump() if isinstance(data, BaseModel) else data
    if delay_time:
        data["delay"] = delay_time

    logger.debug(f"message_id={message_id}, data: {repr(data)}")

    credentials = PlainCredentials(
        username=settings.rabbitmq_username,
        password=settings.rabbitmq_password,
    )
    parameters = ConnectionParameters(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        virtual_host=settings.rabbitmq_vhost,
        credentials=credentials,
    )
    rmq_connection = BlockingConnection(parameters=parameters)
    rmq_channel = rmq_connection.channel()

    rmq_channel.exchange_declare(
        exchange_name,
        "x-delayed-message" if delay_time else ExchangeType.DIRECT,
        durable=True,
        # auto_delete=True,
        arguments={"x-delayed-type": "direct"} if delay_time else None,
    )

    rmq_channel.queue_declare(
        queue_name,
        durable=True,
        # auto_delete=True,
    )

    rmq_channel.queue_bind(queue_name, exchange_name)

    rmq_channel.basic_publish(
        exchange=exchange_name,
        routing_key=routing_key,
        body=json.dumps(data).encode(),
        properties=BasicProperties(
            app_id=app_id,
            headers={"x-delay": delay_time} if delay_time else None,
            message_id=message_id,
        ),
    )
    logger.info(
        f"exchange_name: {exchange_name}, queue_name: {queue_name}, routing_key: {routing_key}, "
        f"app_id: {app_id}, message_id: {message_id}, data: {repr(data)}"
    )
