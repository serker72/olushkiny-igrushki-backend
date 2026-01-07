from functools import wraps
from inspect import iscoroutinefunction
from typing import Any, Callable, Optional

from loguru import logger
from redis import Redis

from common.helpers.redis import get_redis
from common.schemas.models.settings import settings


def task_lock(
    lock_key: str,
    redis_client: Redis = get_redis(),
    ttl: int = settings.task_lock_timeout,
    timeout: int = 0,
    is_silently: bool = True,
    is_delete: bool = True,
):
    """
    Декоратор для блокировки запуска следующего экземпляра, пока не завершился предыдущий

    Args:
        lock_key: ключ для блокировки
        redis_client: redis клиент
        ttl: время жизни блокировки в секундах (защита от зависания)
        timeout: время ожидания блокировки в секундах (0 - не ждать)
        is_silently: True - возвращает None, если не может получить блокировку, False - выводит исключение
        is_delete: True - флаг удаления блокировки после завершения
    """

    def decorator(func: Callable) -> Callable:
        def shared_logic(*args, **kwargs):
            block = redis_client.set(f"task_lock:{lock_key}", "1", nx=True, ex=ttl)

            if not block:
                if timeout > 0:
                    import time

                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        block = redis_client.set(f"task_lock:{lock_key}", "1", nx=True, ex=ttl)
                        if block:
                            break
                        time.sleep(0.1)  # пауза перед повторной попыткой

                if not block:
                    message = f"Не удалось получить блокировку '{lock_key}' для функции {func.__name__}"
                    if is_silently:
                        logger.warning(message)
                        return None
                    else:
                        raise Exception(message)

            return block

        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[Any]:
            block = shared_logic(*args, **kwargs)
            if not block:
                return None

            try:
                logger.info(f"Блокировка '{lock_key}' получена, выполняем {func.__name__}")
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Ошибка в функции {func.__name__} с блокировкой '{lock_key}': {str(e)}")
                raise
            finally:
                if is_delete:
                    try:
                        redis_client.delete(f"task_lock:{lock_key}")
                        logger.info(f"Блокировка '{lock_key}' освобождена")
                    except Exception as e:
                        logger.error(f"Ошибка при освобождении блокировки '{lock_key}': {str(e)}")

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            block = shared_logic(*args, **kwargs)
            if not block:
                return None

            try:
                logger.info(f"Блокировка '{lock_key}' получена, выполняем {func.__name__}")
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Ошибка в функции {func.__name__} с блокировкой '{lock_key}': {str(e)}")
                raise
            finally:
                if is_delete:
                    try:
                        redis_client.delete(f"task_lock:{lock_key}")
                        logger.info(f"Блокировка '{lock_key}' освобождена")
                    except Exception as e:
                        logger.error(f"Ошибка при освобождении блокировки '{lock_key}': {str(e)}")

        return async_wrapper if iscoroutinefunction(func) else wrapper

    return decorator
