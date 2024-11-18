from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class EmailData(BaseModel):
    prompt_template: str
    subject: str
    schedule_time: Optional[str]
    batch_size: int = 50
    interval_minutes: int = 60
    throttle_rate: str = 'hourly'

class EmailStatus(BaseModel):
    tracking_id: str
    to_email: str
    subject: str
    status: str
    delivery_status: str
    scheduled_time: Optional[datetime]
    sent_time: Optional[datetime]