import redis
import pandas as pd
import json
from typing import List, Dict
import os
import logging
import io

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                decode_responses=True
            )
            self.redis_client.ping()  # Test connection
        except redis.ConnectionError as e:
            raise Exception(f"Failed to connect to Redis: {str(e)}")

    async def store_csv_data(self, csv_data: pd.DataFrame) -> bool:
        try:
            # Validate DataFrame
            if csv_data.empty:
                raise ValueError("CSV data is empty")

            # Convert to JSON and store
            json_data = csv_data.to_json(orient='records')
            pipe = self.redis_client.pipeline()
            
            # Store data with expiration (24 hours)
            pipe.set('current_csv_data', json_data)
            pipe.expire('current_csv_data', 86400)  # 24 hours
            
            # Store fields with expiration
            pipe.set('csv_fields', json.dumps(list(csv_data.columns)))
            pipe.expire('csv_fields', 86400)  # 24 hours
            
            pipe.execute()
            return True
            
        except Exception as e:
            logger.error(f"Error storing CSV data: {str(e)}")
            return False

    async def get_csv_data(self) -> List[Dict]:
        try:
            data = self.redis_client.get('current_csv_data')
            return json.loads(data) if data else []
        except Exception:
            return []

    async def get_csv_fields(self) -> List[str]:
        try:
            fields = self.redis_client.get('csv_fields')
            return json.loads(fields) if fields else []
        except Exception:
            return []

    async def get_csv_preview(self, num_rows=5):
        try:
            data = self.redis_client.get('current_csv_data')
            if not data:
                return None
            df = pd.read_json(io.StringIO(data), orient='records')
            return df.head(num_rows).to_dict('records')
        except Exception as e:
            logger.error(f"Error getting CSV preview: {str(e)}")
            return None