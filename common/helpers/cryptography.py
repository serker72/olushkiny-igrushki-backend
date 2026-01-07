from base64 import b64encode
from contextlib import suppress

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes, PublicKeyTypes

from .file import get_file_content


def get_private_key(file_path: str, private_key_password: bytes = None) -> PrivateKeyTypes:
    """Загрузить приватный ключ сервера из файла PEM"""
    return serialization.load_pem_private_key(
        get_file_content(file_path),
        password=private_key_password,
        backend=default_backend(),
    )


def get_public_key(file_path: str) -> PublicKeyTypes:
    """Загрузить публичный ключ сервера из файла PUB"""
    return serialization.load_pem_public_key(get_file_content(file_path), backend=default_backend())


def get_public_key_base64(file_path: str) -> str:
    """Загрузить публичный ключ сервера из файла PUB в формате BASE64"""
    return b64encode(get_file_content(file_path)).decode("utf-8")


def get_public_key_from_string(key_string: str) -> PublicKeyTypes:
    """Загрузить публичный ключ сервера из строки"""
    return serialization.load_pem_public_key(bytes(key_string), backend=default_backend())


def encrypt_message(public_key: PublicKeyTypes, message: str) -> bytes:
    """Шифровать сообщение публичным ключом сервера"""
    public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
        # format=serialization.PublicFormat.PKCS1
    )

    ciphertext = public_key.encrypt(
        message.encode("utf-8"),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        # padding.PKCS1v15()
    )

    return ciphertext


def decrypt_message(private_key: PrivateKeyTypes, ciphertext: bytes) -> str | None:
    """Расшифровать сообщение приватным ключом сервера"""
    private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    with suppress(Exception):
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
            # padding.PKCS1v15()
        )
        return plaintext.decode("utf-8")


def create_message_signature(private_key: PrivateKeyTypes, message: str) -> bytes:
    """Создать цифровую подпись сообщения приватным ключом сервера"""
    private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    signature = private_key.sign(
        message.encode("utf-8"),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )

    return signature


def verify_message_signature(public_key: PublicKeyTypes, message: str, signature: bytes) -> bool:
    """Проверить цифровую подпись сообщение публичным ключом сервера"""
    public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
        # format=serialization.PublicFormat.PKCS1
    )

    try:
        public_key.verify(
            signature,
            message.encode("utf-8"),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )

        return True
    except InvalidSignature:
        return False
