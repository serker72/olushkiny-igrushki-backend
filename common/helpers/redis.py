from redis import ConnectionPool, Redis

from common.schemas.models.settings import settings

# Синхронный пул подключений к Redis
redis_connection_pool = ConnectionPool.from_url(
    settings.get_redis_url(),
    decode_responses=True,
)


def get_redis() -> Redis:
    """Получение синхронного подключения к Redis"""
    return Redis(connection_pool=redis_connection_pool)
