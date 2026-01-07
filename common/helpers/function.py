from asyncio import iscoroutinefunction
from typing import Any, Callable


async def execute_function(func: Callable, *args, **kwargs) -> Any:
    """
    Выполнение указанной функции с указанными параметрами:

    - выполнение проверки на асинхронность указанной функции;
    - выполнение указанной функции с указанными параметрами;
    - возврат результатов выполнения функции.
    """
    return await func(*args, **kwargs) if iscoroutinefunction(func) else func(*args, **kwargs)


async def execute_function_default(func: Callable | None, func_default: Callable, *args, **kwargs) -> Any:
    """
    Выполнение указанной функции или функции по умолчанию с указанными параметрами:

    - определение функции для выполнения - указанная функция или функция по умолчанию
    - выполнение проверки на асинхронность функции;
    - выполнение функции с указанными параметрами;
    - возврат результатов выполнения функции.
    """
    return await execute_function(func if callable(func) else func_default, *args, **kwargs)
