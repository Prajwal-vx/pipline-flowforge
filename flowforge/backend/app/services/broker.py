import json
from collections import defaultdict
from redis.asyncio import Redis
from app.core.config import settings

redis = Redis.from_url(settings.redis_url, decode_responses=True)
_subscribers = defaultdict(set)

async def publish(execution_id: str, event: dict):
    await redis.publish(f"execution:{execution_id}", json.dumps(event, default=str))

async def healthcheck() -> bool:
    try:
        return bool(await redis.ping())
    except Exception:
        return False
