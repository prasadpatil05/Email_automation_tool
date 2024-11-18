import redis
import pandas as pd
from datetime import datetime, timedelta
from rq import Queue
from rq_scheduler import Scheduler
from .esp_utils import ESPService
import os
import logging
import uuid

from io import StringIO
logger = logging.getLogger(__name__)

class EmailScheduler:
    def __init__(self):
        self.redis_conn = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0))
        )
        self.queue = Queue(connection=self.redis_conn)
        self.scheduler = Scheduler(queue=self.queue, connection=self.redis_conn)
        self.esp_service = ESPService()

    async def process_email_batch(self, batch_data: list, template: str, subject: str):
        for row in batch_data:
            tracking_id = str(uuid.uuid4())
            content = template
            
            # Replace placeholders
            for key, value in row.items():
                content = content.replace(f"{{{key}}}", str(value))
                subject = subject.replace(f"{{{key}}}", str(value))

            # Send email
            result = await self.esp_service.send_email(
                to_email=row['email'],
                subject=subject,
                content=content,
                tracking_id=tracking_id
            )

            # Store email status
            self.redis_conn.hset(
                f"email:{tracking_id}",
                mapping={
                    'to_email': row['email'],
                    'status': result['status'],
                    'delivery_status': 'pending',
                    'sent_time': datetime.now().isoformat()
                }
            )

    async def schedule_batch(self, prompt_template: str, subject: str, schedule_time: str,
                           batch_size: int, interval_minutes: int) -> str:
        try:
            csv_data = self.redis_conn.get('current_csv_data')
            df = pd.read_csv(StringIO(csv_data.decode('utf-8')))
            
            total_records = len(df)
            batch_count = (total_records + batch_size - 1) // batch_size
            
            job_ids = []
            schedule_dt = datetime.fromisoformat(schedule_time)
            
            for i in range(batch_count):
                start_idx = i * batch_size
                end_idx = min((i + 1) * batch_size, total_records)
                batch_df = df.iloc[start_idx:end_idx]
                
                batch_time = schedule_dt + timedelta(minutes=i * interval_minutes)
                
                job = self.scheduler.enqueue_at(
                    batch_time,
                    self.process_email_batch,
                    args=[batch_df.to_dict('records'), prompt_template, subject],
                    job_id=f"email_batch_{i}"
                )
                job_ids.append(job.id)
            
            return job_ids[0]  # Return first job ID as reference
            
        except Exception as e:
            logger.error(f"Error in schedule_batch: {str(e)}")
            raise