import hashlib
import os
from mimetypes import guess_extension
from pathlib import Path

import magic


def get_file_hash(file_path: str | Path) -> str:
    """Получение хеша содержимого файла"""
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    return file_hash.hexdigest()


def get_file_content(file_path: str | Path) -> bytes:
    """Получение содержимого файла"""
    with open(file_path, "rb") as f:
        return f.read()


def get_file_content_mime_type(file_content: bytes) -> str:
    """Получение типа файла по его содержимому"""
    return magic.from_buffer(file_content, mime=True)


def get_file_mime_type(file_path: str | Path) -> str:
    """Получение типа файла"""
    return magic.from_file(file_path, mime=True)


def get_file_extension(file_path: str | Path) -> str:
    """Получение расширения файла"""
    f_name, f_extension = os.path.splitext(file_path)
    return guess_extension(get_file_mime_type(file_path)) if not f_extension else f_extension


def check_directory_exists(file_path: str | Path) -> bool:
    """Проверка существования каталога"""
    return os.path.isdir(file_path)


def check_directory_writable(file_path: str | Path) -> bool:
    """Проверка доступности каталога для записи"""
    return os.access(file_path, os.W_OK)


def check_file_exists(file_name: str | Path) -> bool:
    """Проверка существования файла"""
    return os.path.isfile(file_name)


def get_file_size(file_path: str | Path) -> int:
    """Получение размера файла"""
    return Path(file_path).stat().st_size


def check_file_mime_type_is_image(mime_type: str) -> bool:
    """Проверка вхождения типа файла в список типов файлов изображений"""
    return mime_type.startswith("image/")
