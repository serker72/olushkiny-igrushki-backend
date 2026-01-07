import traceback


def get_traceback(exception: Exception) -> str:
    """Получение сообщения об ошибке с трассировкой"""
    return "".join(traceback.format_exception(exception))
