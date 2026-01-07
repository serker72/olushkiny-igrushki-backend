from uuid import uuid4

from fastapi import Request


def get_client_ip_from_fastapi_request(request: Request) -> str:
    """Получение IP адреса клиента из запроса FastAPI"""
    return (request.headers.get("x-forwarded-for") or request.client.host).split(",")[0]


def get_client_user_agent_from_fastapi_request(request: Request) -> str:
    """Получение User-Agent клиента из запроса FastAPI"""
    return request.headers.get("user-agent")


def build_multipart_boundary() -> str:
    """Построение значения директивы boundary"""
    return f"boundary={'-' * 23}{uuid4().hex}"
