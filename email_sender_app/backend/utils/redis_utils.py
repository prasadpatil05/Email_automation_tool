import redis
import os
from typing import Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0))
        )

    async def store_email_status(self, tracking_id: str, status_data: Dict[str, Any]):
        try:
            self.redis_client.hset(
                f"email:{tracking_id}",
                mapping=status_data
            )
        except Exception as e:
            logger.error(f"Error storing email status: {str(e)}")
            raise

    async def get_email_status(self, tracking_id: str) -> Dict[str, Any]:
        try:
            status = self.redis_client.hgetall(f"email:{tracking_id}")
            return {k.decode(): v.decode() for k, v in status.items()}
        except Exception as e:
            logger.error(f"Error getting email status: {str(e)}")
            raise 