import aioredis
import logging

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

async def get_redis():
    """Return a shared aioredis connection, creating it on first call. Returns None if Redis is unavailable."""
    if not hasattr(get_redis, "redis"):
        try:
            get_redis.redis = await aioredis.from_url(
                settings.REDIS_URL or "redis://localhost"
            )
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}")
            return None
    return get_redis.redis

async def add_to_blacklist(jti: str, exp: int):
    """Add a token JTI to the Redis blacklist with a TTL matching its expiry. Silently no-ops if Redis is down."""
    try:
        redis = await get_redis()
        if redis is None:
            return
        await redis.set(f"blacklist:{jti}", "1", ex=exp)
    except Exception as e:
        logger.warning(f"Could not add token to blacklist: {e}")

async def is_blacklisted(jti: str) -> bool:
    """Return True if the token JTI has been blacklisted. Fails open (returns False) if Redis is unavailable."""
    try:
        redis = await get_redis()
        if redis is None:
            return False
        return await redis.exists(f"blacklist:{jti}")
    except Exception as e:
        logger.warning(f"Could not check token blacklist: {e}")
        return False  # Fail open — don't reject valid tokens if Redis is down
    