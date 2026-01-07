import argparse
import asyncio

import uvloop
from loguru import logger
from pydantic import ValidationError

from app_backend.services.base import ServiceManager
from app_queue_processing import workers
from common.exceptions import MethodNotAllowedException
from common.helpers import constants as c
from common.helpers.classes import get_class_properties
from common.helpers.database import get_sa_async_engine
from common.helpers.log import logger_configure
from common.schemas.models.settings import settings

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LevelCraft: RabbitMQ queue worker running script")
    parser.add_argument(
        "-q",
        "--queue-name",
        help="Queue name",
        required=True,
    )
    parser.add_argument(
        "-c",
        "--class-name",
        help="Worker class name",
        required=True,
    )
    parser.add_argument(
        "-i",
        "--worker-id",
        help="Worker ID: default - 1",
        default=1,
        type=lambda x: int(x),
    )
    parser.add_argument(
        "-t",
        "--reconnect-timeout",
        help="Worker reconnect timeout: default - 2",
        default=2,
        type=lambda x: int(x),
    )
    parser.add_argument(
        "-l",
        "--consume-method-is-lock",
        help="Worker consume method is lock (1/0): default - 0",
        default=False,
        type=lambda x: True if x == "1" else False,
    )
    parser.add_argument(
        "-lt",
        "--consume-method-lock-ttl",
        help="Worker consume method lock TTL: default - 60",
        default=60,
        type=lambda x: int(x),
    )
    parser.add_argument(
        "-ld",
        "--consume-method-lock-is-delete",
        help="Worker consume method lock is delete (1/0): default - 0",
        default=False,
        type=lambda x: True if x == "1" else False,
    )
    parser.add_argument(
        "-dt",
        "--message-delay-time",
        help="Message delay time in seconds: default - 0",
        default=0,
        type=lambda x: int(x),
    )

    args = parser.parse_args()

    logger_configure(c.APPLICATION_CODE_QUEUE_PROCESSING, f"worker.{args.queue_name}.{args.worker_id}")

    logger.info(
        f"queue_name: {args.queue_name}, worker_id: {args.worker_id}, "
        f"class_name: {args.class_name}, reconnect_timeout: {args.reconnect_timeout}, "
        f"consume_method_is_lock: {args.consume_method_is_lock}, "
        f"consume_method_lock_ttl: {args.consume_method_lock_ttl}, "
        f"consume_method_lock_is_delete: {args.consume_method_lock_is_delete}, "
    )

    if not hasattr(workers, args.class_name):
        exception = MethodNotAllowedException(
            code="class_not_implemented", message_context={"class_name": args.class_name}
        )
        logger.error(exception.get_content().message)
        raise exception

    worker_class = getattr(workers, args.class_name)
    worker_class_properties = get_class_properties(worker_class)
    logger.debug(f"worker_class_properties: {repr(worker_class_properties)}")

    try:
        with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
            worker = worker_class(
                settings=settings,
                service_manager=ServiceManager(settings=settings),
                queue_name=args.queue_name,
                worker_id=args.worker_id,
                reconnect_timeout=args.reconnect_timeout,
                consume_method_is_lock=args.consume_method_is_lock,
                consume_method_lock_ttl=args.consume_method_lock_ttl,
                consume_method_lock_is_delete=args.consume_method_lock_is_delete,
                message_delay_time=args.message_delay_time,
            )

            if "engine" in worker_class_properties:
                worker.engine = get_sa_async_engine()
                logger.debug(f"worker.engine: {repr(worker.engine)}")

            runner.run(worker.run())
    except ValidationError as e:
        logger.error(e)
    except KeyboardInterrupt:
        logger.info("Main task keyboard interrupt")
    except Exception as e:
        logger.error(e)
        # logger.error("Something unexpected happened")
    finally:
        logger.info("Shutdown complete")
