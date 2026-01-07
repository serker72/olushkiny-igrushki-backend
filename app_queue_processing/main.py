import asyncio
import subprocess
from collections import defaultdict
from os.path import join

import uvloop
from loguru import logger
from pydantic import ValidationError

from common.helpers import constants as c
from common.helpers.exception import get_traceback
from common.helpers.log import logger_configure
from common.schemas.models.settings import BASE_PATH, QueueParam, settings

script_file = join(BASE_PATH, "app_queue_processing", "worker_runner.py")
queue_workers = defaultdict(dict)


def get_app_queue_workers(queue_name: str) -> dict:
    """Получение списка процессов обработчиков указанной очереди"""
    workers = defaultdict(str)
    args = [
        "ps",
        "h",
        "-eo",
        "pid:1,command",
    ]
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, _ = process.communicate()
    for line in stdout.splitlines():
        pid, cmdline = line.decode("utf-8").strip().split(" ", 1)
        if cmdline.find(f"-q={queue_name}") > -1:
            workers[int(pid)] = cmdline

    logger.debug(f"queue_name: {queue_name}, workers: {repr(workers)}")
    return workers


def run_app_queue_worker(item: QueueParam, worker_id: int):
    """Запуск обработчика для указанной очереди"""
    args = [
        settings.queue_processing_python_interpreter,
        script_file,
        f"-q={item.queue_name}",
        f"-c={item.worker_param.class_name}",
        f"-i={worker_id}",
        f"-t={item.worker_param.reconnect_timeout}",
        f"-l={int(item.worker_param.consume_method_is_lock)}",
        f"-lt={item.worker_param.consume_method_lock_ttl}",
        f"-ld={int(item.worker_param.consume_method_lock_is_delete)}",
        f"-dt={item.message_delay_time}",
    ]

    try:
        p = subprocess.Popen(args=args, cwd=BASE_PATH)
    except Exception as e:
        logger.error(f"queue_name: {item.queue_name}, worker_id: {worker_id}, error: {e}")
    else:
        queue_workers[item.queue_name][worker_id] = p.pid
        logger.debug(f"queue_name: {item.queue_name}, worker_id: {worker_id}, pid: {p.pid}")


async def main():
    while True:
        for item in settings.queue_processing_queues.values():
            workers = get_app_queue_workers(item.queue_name) if item.queue_name in queue_workers.keys() else {}

            logger.debug(f"queue_name: {item.queue_name}, worker_count: {item.worker_count}, workers: {repr(workers)}")

            for worker_id in range(1, item.worker_count + 1):
                if (
                    item.queue_name not in queue_workers.keys()
                    or worker_id not in queue_workers[item.queue_name].keys()
                    or queue_workers[item.queue_name][worker_id] not in workers.keys()
                ):
                    run_app_queue_worker(item, worker_id)
                # else:
                #     logger.info(
                #         f"queue_name: {item.queue_name}, worker_id: {worker_id}, "
                #         f"pid: {queue_workers[item.queue_name][worker_id]}"
                #     )

        logger.info(f"queue_workers: {repr(queue_workers)}")

        await asyncio.sleep(settings.queue_processing_processing_timeout)

    # await asyncio.Future()


if __name__ == "__main__":
    logger_configure(c.APPLICATION_CODE_QUEUE_PROCESSING, "main")

    try:
        with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
            runner.run(main())
    except ValidationError as e:
        logger.error(e)
    except KeyboardInterrupt:
        logger.info("Main task keyboard interrupt")
    except Exception as e:
        trace = get_traceback()
        logger.error(f"{e}\n{trace}")
        # logger.error("Something unexpected happened")
    finally:
        logger.info("Shutdown complete")
