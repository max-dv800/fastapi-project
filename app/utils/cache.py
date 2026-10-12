import datetime
import json
from decimal import Decimal
from uuid import UUID

from redis.asyncio import from_url

from app.core.config import settings


def serialize_date_json(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return obj.hex
    if isinstance(obj, Decimal):
        return str(obj)

    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class CacheRedis:
    def __init__(self):
        self._client = from_url(settings.redis_url)

    async def set(self, key, val, ex, nx=False):
        await self._client.set(key, json.dumps(val, default=serialize_date_json), ex=ex)

    async def get(self, key):
        val = await self._client.get(key)
        if val is not None:
            return json.loads(val)

    async def delete(self, key):
        await self._client.delete(key)

    async def exists(self, key):
        return await self._client.exists(key)
