from redis.asyncio import ConnectionPool, Redis

from common.schemas.models.settings import settings

# Асинхронный пул подключений к Redis
redis_async_connection_pool = ConnectionPool.from_url(
    settings.get_redis_url(),
    decode_responses=True,
)


async def get_async_redis() -> Redis:
    """Получение асинхронного подключения к Redis"""
    return await Redis(connection_pool=redis_async_connection_pool)
