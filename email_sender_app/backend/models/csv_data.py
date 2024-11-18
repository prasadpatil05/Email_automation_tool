from pydantic import BaseModel
from typing import List

class CSVUploadResponse(BaseModel):
    message: str
    fields: List[str]
    total_records: int 